"""MiniMax Hailuo API adapter; offline request preparation and explicit paid boundary."""
import copy
from datetime import datetime, timezone
import ipaddress
import os
from pathlib import Path
import socket
import time
import uuid
from urllib.parse import urlencode, urlsplit

from vge_core import ContractError, require, negotiate, digest, save, number
from vge_runtime import ComfyClient


def _journal_uncertain(run, attempt_id, error):
    try:
        save(run/'submission-uncertain.json', {'attempt_id':attempt_id,'status':'UNKNOWN','error':type(error).__name__,
             'next_action':'Inspect provider task/account by request hash; never automatically resubmit'})
    except (OSError, TypeError, ValueError):
        pass


def _approved_image_url(value):
    require(isinstance(value, str) and value, 'First-frame URL is required')
    url = urlsplit(value)
    require(url.scheme == 'https' and url.hostname and not url.username and not url.password and not url.query and not url.fragment,
            'Use an approved public HTTPS first-frame URL without embedded credentials; other input forms require a separately reviewed adapter')
    host = url.hostname.lower()
    require(host not in ('localhost',) and not host.endswith('.local'), 'First-frame URL must not target a local host')
    try:
        addresses = {ipaddress.ip_address(item[4][0]) for item in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)}
    except (OSError, ValueError) as exc:
        raise ContractError('First-frame URL host could not be resolved safely') from exc
    require(addresses and all(address.is_global for address in addresses),
            'First-frame URL must resolve only to globally routable addresses')
    return value


def hailuo_request(spec):
    """Prepare from reviewed prompt; never truncate canonical meaning to an API limit."""
    require(isinstance(spec, dict), 'MiniMax request spec must be an object')
    profile, shot = spec.get('profile'), spec.get('shot')
    require(isinstance(profile, dict) and isinstance(shot, dict), 'MiniMax request needs profile and shot objects')
    require(profile.get('provider') == 'minimax_api', 'Expected MiniMax API profile')
    prompt = spec.get('prompt')
    require(isinstance(prompt, str) and 0 < len(prompt) <= 2000, 'Provide a reviewed prompt of 1..2000 characters; record omissions rather than truncating')
    model = profile.get('model')
    require(model in ('MiniMax-Hailuo-2.3', 'MiniMax-Hailuo-2.3-Fast', 'MiniMax-Hailuo-02'), 'Model is outside this adapter contract')
    mode = shot.get('generation_mode')
    require(mode in ('T2V','I2V'), 'This adapter supports only its documented T2V/I2V subset')
    require(model != 'MiniMax-Hailuo-2.3-Fast' or mode == 'I2V', 'Fast profile requires an image')
    duration = shot.get('duration_s'); resolution = spec.get('resolution')
    require(type(duration) is int and duration in (6,10), 'Hailuo request duration must be 6 or 10 seconds')
    require(resolution in ('768P','1080P') and (resolution != '1080P' or duration == 6), 'Unsupported duration/resolution pair')
    body = {'model':model,'prompt':prompt,'duration':duration,'resolution':resolution,'prompt_optimizer':False}
    if mode == 'I2V':
        image = spec.get('first_frame_image','')
        _approved_image_url(image)
        body['first_frame_image'] = image
    compatibility = negotiate(shot, profile)
    return {'schema_version':1,'provider':'minimax_api','endpoint':'https://api.minimax.io', 'route':'/v1/video_generation',
            'method':'POST','body':body,'request_hash':digest(body),'compatibility':compatibility,
            'mode':'PLAN_ONLY','limitations':['Account access, media-transfer rights and actual provider execution require separate evidence']}


def hailuo_submit(spec, destination, paid_authorized=False, transfer_authorized=False, client=None):
    require(paid_authorized is True, 'Paid API submission requires explicit cost/target authorization')
    request = hailuo_request(spec)
    require(request['compatibility']['status'] == 'SUPPORTED', 'Provider feature profile must be confirmed before paid submission')
    if spec['shot']['generation_mode'] == 'I2V':
        provenance = spec.get('reference_provenance', {})
        require(isinstance(provenance, dict), 'Image transfer requires reference provenance')
        require(transfer_authorized is True and provenance.get('rights_status') in ('CONFIRMED', 'NOT_APPLICABLE'), 'Image transfer requires scoped authorization and reference rights')
        require(provenance.get('consent_status') in ('CONFIRMED', 'NOT_APPLICABLE'), 'Image transfer requires explicit consent status')
        flags = ('reference_sensitive', 'likeness_or_voice')
        for flag in flags:
            if flag in spec:
                require(type(spec[flag]) is bool, f'{flag} must be boolean')
        risky_roles = {'character_identity', 'face', 'likeness', 'voice', 'voice_identity', 'identity_reference'}
        roles = provenance.get('roles', spec.get('reference_roles', []))
        require(isinstance(roles, list) and all(isinstance(role, str) and role for role in roles), 'Reference roles must be an array of nonempty strings')
        sensitive = bool(spec.get('reference_sensitive')) or bool(spec.get('likeness_or_voice')) or bool(risky_roles.intersection(roles))
        if sensitive:
            require(provenance.get('rights_status') == 'CONFIRMED', 'Sensitive image transfer requires confirmed rights scope')
            require(provenance.get('consent_status') == 'CONFIRMED', 'Sensitive image transfer requires scoped consent')
    if client is None:
        token = os.environ.get('MINIMAX_API_KEY')
        require(bool(token), 'MINIMAX_API_KEY must be provided outside request artifacts')
        client = ComfyClient(request['endpoint'], remote=True, token=token)
    run_id = 'attempt_' + uuid.uuid4().hex
    run = Path(destination)/run_id;run.mkdir(parents=True,exist_ok=False)
    record = {'schema_version':1,'id':run_id,'revision':1,'shot_id':spec['shot']['id'],'provider':'minimax_api','status':'UNKNOWN',
              'started_at':datetime.now(timezone.utc).isoformat(),'profile':{'id':spec['profile']['id'],'revision':spec['profile']['profile_revision']},
              'request_hash':request['request_hash'],'task_id':None,'limitations':['Provider model weight/runtime provenance may be unavailable; this transport record alone is not an acceptance-eligible ExecutionAttempt']}
    save(run/'request.json',request)
    save(run/'submission-001.json',record)
    # Exactly one POST. A transport failure keeps the immutable UNKNOWN record.
    try:
        reply=client.request(request['route'],request['body'])
        require(isinstance(reply, dict), 'Provider response must be an object')
        accepted = reply.get('base_resp', {})
        require(isinstance(accepted, dict), 'Provider response status is malformed')
        require(accepted.get('status_code') == 0 and isinstance(reply.get('task_id'), str) and reply['task_id'], 'Provider rejected submission; inspect provider account before retry')
        submitted=copy.deepcopy(record);submitted.update(revision=2,supersedes_hash=digest(record),task_id=reply['task_id'],status='SUBMITTED')
        save(run/'submission-002.json',submitted)
    except Exception as exc:
        _journal_uncertain(run, run_id, exc)
        if isinstance(exc, ContractError):
            raise
        raise ContractError('Provider submission outcome or journal is uncertain; inspect the same task before retry') from exc
    return {'submission':submitted,'run_directory':str(run.resolve())}


def hailuo_poll(task_id, timeout=60, interval=2, client=None):
    require(number(timeout,True) and timeout <= 3600 and number(interval,True), 'Invalid poll budget')
    require(isinstance(task_id,str) and task_id, 'Task ID required')
    if client is None:
        token=os.environ.get('MINIMAX_API_KEY');require(bool(token),'MINIMAX_API_KEY required')
        client=ComfyClient('https://api.minimax.io',remote=True,token=token)
    deadline=time.monotonic()+timeout
    while True:
        reply=client.request('/v1/query/video_generation?'+urlencode({'task_id':task_id}))
        require(isinstance(reply, dict), 'Provider query response must be an object')
        base_resp = reply.get('base_resp', {})
        require(isinstance(base_resp, dict), 'Provider query status is malformed')
        require(base_resp.get('status_code') == 0, 'Provider query failed')
        status=reply.get('status')
        if status in ('Success','Fail'):
            return {'status':'SUCCEEDED' if status=='Success' else 'FAILED','task_id':task_id,'file_id':reply.get('file_id'),
                    'next_action':'Retrieve through the authenticated provider file API; hash bytes and create artifact/observation records before acceptance'}
        remaining=deadline-time.monotonic()
        if remaining <= 0:return {'status':'UNKNOWN','task_id':task_id,'next_action':'Query this same task ID; do not resubmit'}
        time.sleep(min(interval,remaining))
