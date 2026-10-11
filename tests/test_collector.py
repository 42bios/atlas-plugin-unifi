import importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('unifi_collector',ROOT/'worker/collector.py');collector=importlib.util.module_from_spec(spec);spec.loader.exec_module(collector)
def fixture():
 return {'stat/device':[{'mac':'00:11:22:33:44:01','name':'Core switch','type':'usw','model':'USW-24','ip':'192.0.2.2','port_table':[{'port_idx':1,'media':'SFP+','speed':10000,'native_vlan':10},{'port_idx':2,'media':'GE','speed':0}],'password':'SECRET'},{'mac':'00:11:22:33:44:02','name':'Office AP','type':'uap','model':'U6-Pro','ip':'192.0.2.3'}],'rest/user':[{'mac':'00:11:22:33:44:03','hostname':'Laptop'},{'mac':'00:11:22:33:44:04','name':'NAS'},{'mac':'00:11:22:33:44:05','name':'Offline phone'}],'stat/sta':[{'mac':'00:11:22:33:44:03','is_wired':False,'ap_mac':'00:11:22:33:44:02','essid':'Home','ip':'192.0.2.20','tx_bytes':42},{'mac':'00:11:22:33:44:04','is_wired':True,'sw_mac':'00:11:22:33:44:01','sw_port':2,'ip':'192.0.2.21'}],'rest/networkconf':[{'_id':'lan','name':'LAN','ip_subnet':'192.0.2.1/24','vlan':10,'x_passphrase':'SECRET'},{'_id':'vlan-only','name':'No subnet','vlan':20}]}
class CollectorTests(unittest.TestCase):
 def test_inventory_and_wireless_observations(self):
  data=collector.collect(fixture().__getitem__,'unifi-test')
  self.assertEqual(len(data['devices']),5);self.assertEqual(len(data['links']),1)
  self.assertEqual(data['links'][0]['type'],'Wi-Fi');self.assertEqual(data['links'][0]['ssid'],'Home')
  self.assertEqual(data['networks'][0]['cidr'],'192.0.2.0/24')
  port=data['devices'][0]['interfaces'][0];self.assertEqual(port['connector'],'SFP+');self.assertEqual(port['speedMbps'],10000);self.assertEqual(port['nativeVlan'],10)
  self.assertNotIn('speedMbps',data['devices'][0]['interfaces'][1])
  self.assertIn('00:11:22:33:44:04',data['devices'][0]['interfaces'][1]['observation']['learnedMacs'])
  self.assertNotIn('SECRET',json.dumps(data));self.assertNotIn('tx_bytes',json.dumps(data))
 def test_failure_aborts_import(self):
  data=fixture();del data['rest/user']
  with self.assertRaises(KeyError):collector.collect(data.__getitem__,'unifi-test')
 def test_duplicate_device_identity_rejected(self):
  data=fixture();data['stat/device'].append(data['stat/device'][0])
  with self.assertRaisesRegex(ValueError,'Duplicate'):collector.collect(data.__getitem__,'unifi-test')
 def test_missing_ap_does_not_invent_connection(self):
  data=fixture();data['stat/sta'][0]['ap_mac']='00:11:22:33:44:ff'
  self.assertEqual(collector.collect(data.__getitem__,'unifi-test')['links'],[])
