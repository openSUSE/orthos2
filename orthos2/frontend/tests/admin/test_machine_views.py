import mock
from data.models import Architecture, Machine, ServerConfig, System
from django.urls import reverse
from django_webtest import WebTest


class ChangeView(WebTest):

    fixtures = [
        'data/fixtures/systems.json',
        'frontend/tests/user/fixtures/users.json',
        'data/fixtures/architectures.json'
    ]

    @mock.patch('data.models.machine.is_dns_resolvable')
    def setUp(self, m_is_dns_resolvable):
        m_is_dns_resolvable.return_value = True

        ServerConfig.objects.create(key='domain.validendings', value='bar.de')

        m1 = Machine()
        m1.pk = 1
        m1.fqdn = 'machine1.foo.bar.de'
        m1.mac_address = '01:AB:22:33:44:55'
        m1.architecture_id = Architecture.Type.X86_64
        m1.system_id = System.Type.BAREMETAL

        m1.save()

        m2 = Machine()
        m1.pk = 2
        m2.fqdn = 'machine2.foo.bar.de'
        m2.mac_address = '02:AB:22:33:44:55'
        m2.architecture_id = Architecture.Type.X86_64
        m2.system_id = System.Type.BMC

        m2.save()

    def test_visible_fieldsets_non_administrative_systems(self):
        """Test for fieldsets."""
        page = self.app.get(reverse('admin:data_machine_change', args=['1']), user='superuser')
        self.assertContains(page, '<h2>VIRTUALIZATION</h2>')

    def test_visible_inlines_non_administrative_systems(self):
        """Test for inlines."""
        page = self.app.get(reverse('admin:data_machine_change', args=['1']), user='superuser')
        self.assertContains(page, '<h2>Serial Console</h2>')
        self.assertContains(page, '<h2>Remote Power</h2>')

    def test_visible_fieldsets_administrative_systems(self):
        """Test for fieldsets."""
        page = self.app.get(reverse('admin:data_machine_change', args=['2']), user='superuser')
        self.assertNotContains(page, '<h2>VIRTUALIZATION</h2>')

    def test_visible_inlines_administrative_systems(self):
        """Test for inlines."""
        page = self.app.get(reverse('admin:data_machine_change', args=['2']), user='superuser')
        self.assertNotContains(page, '<h2>Serial Console</h2>')
        self.assertNotContains(page, '<h2>Remote Power</h2>')
