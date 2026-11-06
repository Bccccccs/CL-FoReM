"""Zero-episode cleanup identity regression; no containers/models invoked."""
import unittest
from unittest.mock import patch
import supervisor

class CleanupIdentityTests(unittest.TestCase):
 def test_ownership_uses_actual_host_uid_gid(self):
  with patch.object(supervisor.os,'getuid',return_value=1004),patch.object(supervisor.os,'getgid',return_value=1004):
   command=supervisor.ownership_command({'container':'new-isolated-run'})
  self.assertIn('chown -R 1004:1004 /output /runlogs',command[3])
  self.assertIn('new-isolated-run',command[3])
 def test_identity_not_assumed_equal_1000(self):
  with patch.object(supervisor.os,'getuid',return_value=2001),patch.object(supervisor.os,'getgid',return_value=2002):
   command=supervisor.ownership_command({'container':'test'})
  self.assertIn('2001:2002',command[3]);self.assertNotIn('1000:1000',command[3])

if __name__=='__main__':unittest.main()
