import json
import requests
import sys
import importlib
import os
from urllib.parse import urljoin, urlencode
requests.packages.urllib3.disable_warnings()

# 每个功能再调用前都会先动态加载一遍config 目的其实是用来刷新whitelist 这里不体现 详见 commands/v/ 下的py

async def sendrequest(path, **args):
    import importlib
    run_path = os.getcwd()
    sys.path.insert(0, run_path)
    config_path = f"commands.v.config"
    if config_path in sys.modules:
        del sys.modules[config_path]
    config = importlib.import_module(config_path)
    method = args.get('method', 'GET').upper()
    custom_params = args.get('params', {})
    post_data = args.get('data', None)
    req_timeout = args.get('timeout', config.timeout)
    base_url = config.panel_url.rstrip('/')
    full_url = urljoin(base_url, path.lstrip('/'))
    base_params = {'apikey': config.api_key}
    request_params = {**base_params, **custom_params}
    headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    try:
        if method == 'GET':
            if request_params:
                full_url += '?' + urlencode(request_params)
            response = requests.get(
                full_url,
                headers=headers,
                timeout=req_timeout,
                verify=False
            )
        
        elif method == 'POST':
            if request_params:
                full_url += '?' + urlencode(request_params)
            response = requests.post(
                full_url,
                headers=headers,
                json=post_data,
                timeout=req_timeout,
                verify=False
            )
        
        else:
            return {
                'success': False,
                'error': f'不支持的请求方法 {method}'
            }
        
        response.raise_for_status()
        try:
            response_data = response.json()
        except json.JSONDecodeError as e:
            return {
                'success': False,
                'error': f'JSON解析失败 {str(e)}',
                'raw_response': response.text,
                'status_code': response.status_code
            }
        
        return {
            'success': True,
            'data': response_data,
            'status_code': response.status_code
        }
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'error': '请求超时',
            'timeout': req_timeout
        }
    except requests.exceptions.ConnectionError:
        return {
            'success': False,
            'error': f'连接失败 {base_url}'
        }
    except requests.exceptions.HTTPError as e:
        return {
            'success': False,
            'error': f'HTTP错误 {str(e)}',
            'status_code': response.status_code,
            'raw_response': response.text
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'未知错误 {str(e)}',
            'error_type': type(e).__name__
        }

async def get_all_instances(page: int = 1, size: int = 200):
    import importlib
    run_path = os.getcwd()
    sys.path.insert(0, run_path)
    config_path = f"commands.v.config"
    if config_path in sys.modules:
        del sys.modules[config_path]
    config = importlib.import_module(config_path)
    result = await sendrequest(
        path='api/service/remote_service_instances',
        method='GET',
        params={'daemonId': config.daemon_id, 'page': page, 'page_size': size}
    )

    if not result['success']:
        return result

    api_response = result['data']['data']
    instance_list = api_response.get('data', [])
    if not isinstance(instance_list, list):
        return {
            'success': False,
            'error': '返回的数据不是列表',
            'raw_data': api_response
        }
    
    status_mapping = {-1: '忙碌',0: '停止',1: '停止中',2: '启动中',3: '运行中'}
    formatted_instances = []
    for instance in instance_list:
        formatted_instances.append({
            'uuid': instance.get('instanceUuid', ''),
            'name': instance.get('config', {}).get('nickname', '未命名'),
            'status_code': instance.get('status', 0),
            'status_text': status_mapping.get(instance.get('status', 0), '未知状态'),
            'online': instance.get('info', {}).get('currentPlayers', 0),
            'max_online': instance.get('info', {}).get('maxPlayers', 0),
            'node_id': instance.get('nodeId', ''),
            'full_info': instance
        })
    return {
        'success': True,
        'count': len(formatted_instances),
        'instances': formatted_instances,
        'raw_data': api_response
    }

async def get_single_instance(instance_uuid):
    import importlib
    run_path = os.getcwd()
    sys.path.insert(0, run_path)
    config_path = f"commands.v.config"
    if config_path in sys.modules:
        del sys.modules[config_path]
    config = importlib.import_module(config_path)
    return await sendrequest(
        path='api/instance',
        method='GET',
        params={
            'daemonId': config.daemon_id,
            'uuid': instance_uuid
        }
    )

async def start_instance(instance_uuid):
    import importlib
    run_path = os.getcwd()
    sys.path.insert(0, run_path)
    config_path = f"commands.v.config"
    if config_path in sys.modules:
        del sys.modules[config_path]
    config = importlib.import_module(config_path)
    return await sendrequest(
        path='api/instance/start',
        method='POST',
        params={'daemonId': config.daemon_id},
        data={'uuid': instance_uuid}
    )