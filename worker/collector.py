"""Inventory whitelist: never exports raw controller configuration or secrets."""
import ipaddress,re

def mac(value):
 value=str(value or '').lower().replace('-',':')
 return value if re.fullmatch(r'(?:[0-9a-f]{2}:){5}[0-9a-f]{2}',value) else ''
def ip(value):
 try:return str(ipaddress.ip_address(value)) if value else ''
 except ValueError:return ''
def collect(get,source,site='default'):
 devices_raw=get('stat/device');active=get('stat/sta');known=get('rest/user');network_raw=get('rest/networkconf')
 devices=[];links=[];networks=[];index={}
 for item in devices_raw:
  key=mac(item.get('mac'))
  if not key:raise ValueError('UniFi device is missing a valid MAC identity')
  if key in index:raise ValueError('Duplicate UniFi device MAC')
  kind={'uap':'Access point','usw':'Switch','ugw':'Router','usg':'Router','udm':'Router','uxg':'Router'}.get(item.get('type'),'Other')
  ports=item.get('port_table') or [];interfaces=[]
  for p in ports:
   number=p.get('port_idx')
   if type(number) is not int or number<1:continue
   media=str(p.get('media',''));connector={'GE':'RJ45','FE':'RJ45','SFP':'SFP','SFP+':'SFP+','SFP28':'SFP28'}.get(media,'Other')
   record={'name':str(number),'label':p.get('name') or 'Port '+str(number),'type':'Fiber' if connector.startswith('SFP') else 'Ethernet','connector':connector,'ips':[]}
   speed=p.get('speed')
   if type(speed) in (int,float) and 0<speed<=1600000:record['speedMbps']=speed
   vlan=p.get('native_vlan')
   if type(vlan) is int and 1<=vlan<=4094:record.update(mode='Access',nativeVlan=vlan)
   peer=mac((p.get('last_connection') or {}).get('mac'))
   if peer:record['observation']={'learnedMacs':[peer]}
   interfaces.append(record)
  record={'id':'device-'+key,'name':item.get('name') or item.get('model') or key,'kind':kind,'manufacturer':'Ubiquiti','model':item.get('model',''),'ip':ip(item.get('ip')),'ports':len(interfaces),'unifi':{'site':site,'mac':key},'interfaces':interfaces}
  index[key]=record;devices.append(record)
 for item in network_raw:
  subnet=item.get('ip_subnet')
  if not subnet:continue
  try:cidr=str(ipaddress.ip_network(subnet,strict=False))
  except ValueError:continue
  vlan=item.get('vlan',0)
  if type(vlan) is not int or not 0<=vlan<=4094:raise ValueError('Invalid UniFi network VLAN')
  networks.append({'id':'network-'+str(item['_id']),'name':item.get('name','UniFi network'),'cidr':cidr,'vlan':vlan})
 clients={}
 for item in known+active:
  key=mac(item.get('mac'))
  if key and key not in index:clients[key]={**clients.get(key,{}),**item}
 connected={mac(x.get('mac')):x for x in active}
 for key,item in sorted(clients.items()):
  online=connected.get(key);wireless=online is not None and online.get('is_wired') is False
  rec={'id':'client-'+key,'name':item.get('name') or item.get('hostname') or key,'kind':'Other','ports':0,'ip':ip(item.get('ip')),'unifi':{'site':site,'mac':key,'objectType':'Client'}}
  if wireless:
   rec['interfaces']=[{'name':'wlan0','type':'Wi-Fi','ips':[rec['ip']] if rec['ip'] else []}]
   ap=index.get(mac(online.get('ap_mac')))
   if ap:links.append({'id':'wifi-'+key,'source':rec['id'],'target':ap['id'],'type':'Wi-Fi','sourcePort':'','targetPort':'','ssid':str(online.get('essid') or '')})
  # Wired attachment is an observation, not proof of a physical patch path.
  if online and online.get('is_wired') is True:
   sw=index.get(mac(online.get('sw_mac')));port=str(online.get('sw_port',''))
   if sw:
    iface=next((i for i in sw['interfaces'] if i['name']==port),None)
    if iface:
     learned=iface.setdefault('observation',{}).setdefault('learnedMacs',[])
     if key not in learned:learned.append(key)
  devices.append(rec)
 return {'schemaVersion':1,'connector':source,'devices':devices,'services':[],'networks':networks,'links':links}
