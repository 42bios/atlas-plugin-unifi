import json,os,sys
from pathlib import Path
root=Path(__file__).parent;sys.path.insert(0,str(root/'worker'))
from api import Client
from collector import collect
from common.runtime import run
config=json.loads(Path(os.environ['ADDIN_CONFIG_FILE']).read_text())
credentials=json.loads(Path(os.environ['ADDIN_CREDENTIAL_FILE']).read_text())
ca=None
if credentials.get('ca'):
 path=Path(os.environ['ADDIN_CONFIG_FILE']).parent/'unifi_ca';path.write_text(credentials['ca']);path.chmod(0o600);ca=str(path)
def snapshot(source):
 client=Client(config['upstreamUrl'],credentials['username'],credentials['password'],config.get('site','default'),config.get('controllerType','os'),ca,config.get('tlsFingerprint'))
 client.login()
 return collect(client.get,source,config.get('site','default'))
run('unifi',snapshot)
