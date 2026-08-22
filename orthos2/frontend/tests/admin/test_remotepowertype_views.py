"""Tests for the RemotePowerType CRUD frontend views."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from orthos2.data.models import (
    BMC,
    Architecture,
    Domain,
    Machine,
    RemotePower,
    RemotePowerDevice,
    RemotePowerType,
    ServerConfig,
    System,
)


class RemotePowerTypeListViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.remotepowertype = RemotePowerType.objects.create(
            name="AcmeRemotePowerType", device="rpowerdevice"
        )

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:remotepowertypes")
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:remotepowertypes")
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_lists_remotepowertypes(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:remotepowertypes")
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"AcmeRemotePowerType" in response.content

    def test_superuser_get_shows_device_count(self) -> None:
        ServerConfig.objects.create(key="domain.validendings", value="orthos2.test")
        domain = Domain.objects.create(
            name="orthos2.test",
            ip_v4="127.0.0.1",
            ip_v6="::1",
            dynamic_range_v4_start="127.0.0.1",
            dynamic_range_v4_end="127.0.0.1",
            dynamic_range_v6_start="::1",
            dynamic_range_v6_end="::1",
        )
        architecture = Architecture.objects.get(name="x86_64")
        RemotePowerDevice.objects.create(
            fqdn="rpower.orthos2.test",
            mac="AA:BB:CC:DD:EE:FF",
            fence_agent=self.remotepowertype,
            architecture=architecture,
            domain=domain,
        )

        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:remotepowertypes")
        response = self.client.get(url)
        assert response.status_code == 200
        # 3 "Dummy ..." RemotePowerTypes are seeded by migration 0048, so the
        # list isn't just our object - look it up instead of indexing [0].
        listed = {
            remotepowertype.pk: remotepowertype
            for remotepowertype in response.context["object_list"]
        }
        assert listed[self.remotepowertype.pk].device_count == 1

    def test_rpowerdevice_backed_machine_is_not_double_counted(self) -> None:
        """
        RemotePower.save() mirrors remote_power_device.fence_agent onto its own
        fence_agent field for "rpowerdevice"-category types, so a machine whose
        RemotePower references a RemotePowerDevice must not be counted twice
        (once via RemotePowerDevice.fence_agent, once via RemotePower.fence_agent).
        """
        ServerConfig.objects.create(key="domain.validendings", value="orthos2.test")
        domain = Domain.objects.create(
            name="orthos2.test",
            ip_v4="127.0.0.1",
            ip_v6="::1",
            dynamic_range_v4_start="127.0.0.1",
            dynamic_range_v4_end="127.0.0.1",
            dynamic_range_v6_start="::1",
            dynamic_range_v6_end="::1",
        )
        architecture = Architecture.objects.get(name="x86_64")
        remotepowerdevice = RemotePowerDevice.objects.create(
            fqdn="rpower.orthos2.test",
            mac="AA:BB:CC:DD:EE:FF",
            fence_agent=self.remotepowertype,
            architecture=architecture,
            domain=domain,
        )
        machine = Machine.objects.create(
            fqdn="rpowered-machine.orthos2.test",
            system=System.objects.get(name="BareMetal"),
            architecture=architecture,
        )
        RemotePower.objects.create(
            machine=machine, remote_power_device=remotepowerdevice
        )

        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:remotepowertypes")
        response = self.client.get(url)
        listed = {
            remotepowertype.pk: remotepowertype
            for remotepowertype in response.context["object_list"]
        }
        assert listed[self.remotepowertype.pk].device_count == 1

    def test_bmc_backed_machine_with_remotepower_row_is_not_double_counted(
        self,
    ) -> None:
        """
        RemotePower.save() mirrors machine.bmc.fence_agent onto its own
        fence_agent field for "bmc"-category types, so a machine with both a
        BMC and a RemotePower row must not be counted twice.
        """
        ServerConfig.objects.create(key="domain.validendings", value="orthos2.test")
        Domain.objects.create(
            name="orthos2.test",
            ip_v4="127.0.0.1",
            ip_v6="::1",
            dynamic_range_v4_start="127.0.0.1",
            dynamic_range_v4_end="127.0.0.1",
            dynamic_range_v6_start="::1",
            dynamic_range_v6_end="::1",
        )
        bmc_type = RemotePowerType.objects.create(name="AcmeBMCType", device="bmc")
        machine = Machine.objects.create(
            fqdn="bmc-host.orthos2.test",
            system=System.objects.get(name="BareMetal"),
            architecture=Architecture.objects.get(name="x86_64"),
        )
        BMC.objects.create(
            machine=machine,
            fqdn="bmc.orthos2.test",
            mac="AA:BB:CC:DD:EE:01",
            fence_agent=bmc_type,
        )
        RemotePower.objects.create(machine=machine)

        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:remotepowertypes")
        response = self.client.get(url)
        listed = {
            remotepowertype.pk: remotepowertype
            for remotepowertype in response.context["object_list"]
        }
        assert listed[bmc_type.pk].device_count == 1

    def test_bmc_backed_device_is_counted(self) -> None:
        ServerConfig.objects.create(key="domain.validendings", value="orthos2.test")
        _ = Domain.objects.create(
            name="orthos2.test",
            ip_v4="127.0.0.1",
            ip_v6="::1",
            dynamic_range_v4_start="127.0.0.1",
            dynamic_range_v4_end="127.0.0.1",
            dynamic_range_v6_start="::1",
            dynamic_range_v6_end="::1",
        )
        bmc_type = RemotePowerType.objects.create(name="AcmeBMCType", device="bmc")
        machine = Machine.objects.create(
            fqdn="bmc-host.orthos2.test",
            system=System.objects.get(name="BareMetal"),
            architecture=Architecture.objects.get(name="x86_64"),
        )
        BMC.objects.create(
            machine=machine,
            fqdn="bmc.orthos2.test",
            mac="AA:BB:CC:DD:EE:01",
            fence_agent=bmc_type,
        )

        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:remotepowertypes")
        response = self.client.get(url)
        listed = {
            remotepowertype.pk: remotepowertype
            for remotepowertype in response.context["object_list"]
        }
        assert listed[bmc_type.pk].device_count == 1

    def test_hypervisor_backed_device_is_counted(self) -> None:
        ServerConfig.objects.create(key="domain.validendings", value="orthos2.test")
        Domain.objects.create(
            name="orthos2.test",
            ip_v4="127.0.0.1",
            ip_v6="::1",
            dynamic_range_v4_start="127.0.0.1",
            dynamic_range_v4_end="127.0.0.1",
            dynamic_range_v6_start="::1",
            dynamic_range_v6_end="::1",
        )
        hypervisor_type = RemotePowerType.objects.create(
            name="AcmeHypervisorType", device="hypervisor"
        )
        host = Machine.objects.create(
            fqdn="host.orthos2.test",
            system=System.objects.get(name="BareMetal"),
            architecture=Architecture.objects.get(name="x86_64"),
        )
        vm = Machine.objects.create(
            fqdn="vm.orthos2.test",
            system=System.objects.get(name="VM KVM"),
            architecture=Architecture.objects.get(name="x86_64"),
            hypervisor=host,
        )
        RemotePower.objects.create(machine=vm, fence_agent=hypervisor_type)

        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:remotepowertypes")
        response = self.client.get(url)
        listed = {
            remotepowertype.pk: remotepowertype
            for remotepowertype in response.context["object_list"]
        }
        assert listed[hypervisor_type.pk].device_count == 1

    def test_filter_by_device_category(self) -> None:
        bmc_type = RemotePowerType.objects.create(name="AcmeBMCType", device="bmc")

        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:remotepowertypes")
        response = self.client.get(url, {"device": "bmc"})
        listed_names = {rpt.name for rpt in response.context["object_list"]}
        assert bmc_type.name in listed_names
        assert self.remotepowertype.name not in listed_names

    def test_device_count_correct_when_architectures_and_systems_restricted(
        self,
    ) -> None:
        """
        `architectures`/`systems` are unrelated M2M relations ("Supported
        Architectures"/"Supported Systems") - restricting a RemotePowerType to
        specific ones must not, via extra JOINs in the same annotate() query,
        inflate the unrelated device_count annotation.
        """
        ServerConfig.objects.create(key="domain.validendings", value="orthos2.test")
        domain = Domain.objects.create(
            name="orthos2.test",
            ip_v4="127.0.0.1",
            ip_v6="::1",
            dynamic_range_v4_start="127.0.0.1",
            dynamic_range_v4_end="127.0.0.1",
            dynamic_range_v6_start="::1",
            dynamic_range_v6_end="::1",
        )
        architecture = Architecture.objects.get(name="x86_64")
        self.remotepowertype.architectures.add(
            architecture, Architecture.objects.get(name="aarch64")
        )
        self.remotepowertype.systems.add(
            System.objects.get(name="BareMetal"), System.objects.get(name="VM KVM")
        )
        RemotePowerDevice.objects.create(
            fqdn="restricted-rpower.orthos2.test",
            mac="AA:BB:CC:DD:EE:10",
            fence_agent=self.remotepowertype,
            architecture=architecture,
            domain=domain,
        )

        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:remotepowertypes")
        response = self.client.get(url)
        listed = {
            remotepowertype.pk: remotepowertype
            for remotepowertype in response.context["object_list"]
        }
        assert listed[self.remotepowertype.pk].device_count == 1

    def test_bmc_device_count_correct_when_architectures_and_systems_restricted(
        self,
    ) -> None:
        ServerConfig.objects.create(key="domain.validendings", value="orthos2.test")
        Domain.objects.create(
            name="orthos2.test",
            ip_v4="127.0.0.1",
            ip_v6="::1",
            dynamic_range_v4_start="127.0.0.1",
            dynamic_range_v4_end="127.0.0.1",
            dynamic_range_v6_start="::1",
            dynamic_range_v6_end="::1",
        )
        bmc_type = RemotePowerType.objects.create(name="AcmeBMCType", device="bmc")
        bmc_type.architectures.add(Architecture.objects.get(name="x86_64"))
        bmc_type.systems.add(System.objects.get(name="BareMetal"))
        machine = Machine.objects.create(
            fqdn="restricted-bmc-host.orthos2.test",
            system=System.objects.get(name="BareMetal"),
            architecture=Architecture.objects.get(name="x86_64"),
        )
        BMC.objects.create(
            machine=machine,
            fqdn="restricted-bmc.orthos2.test",
            mac="AA:BB:CC:DD:EE:11",
            fence_agent=bmc_type,
        )

        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:remotepowertypes")
        response = self.client.get(url)
        listed = {
            remotepowertype.pk: remotepowertype
            for remotepowertype in response.context["object_list"]
        }
        assert listed[bmc_type.pk].device_count == 1


class RemotePowerTypeDetailViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.remotepowertype = RemotePowerType.objects.create(
            name="AcmeRemotePowerType"
        )

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse(
            "frontend:remotepowertype_detail",
            kwargs={"id": self.remotepowertype.pk},
        )
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:remotepowertype_detail",
            kwargs={"id": self.remotepowertype.pk},
        )
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_detail_page(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:remotepowertype_detail",
            kwargs={"id": self.remotepowertype.pk},
        )
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"AcmeRemotePowerType" in response.content

    def test_nonexistent_remotepowertype_returns_404(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:remotepowertype_detail", kwargs={"id": 99999})
        response = self.client.get(url)
        assert response.status_code == 404


class RemotePowerTypeDevicesViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.remotepowertype = RemotePowerType.objects.create(
            name="AcmeRemotePowerType", device="rpowerdevice"
        )
        self.other_remotepowertype = RemotePowerType.objects.create(
            name="OtherRemotePowerType", device="rpowerdevice"
        )
        ServerConfig.objects.create(key="domain.validendings", value="orthos2.test")
        domain = Domain.objects.create(
            name="orthos2.test",
            ip_v4="127.0.0.1",
            ip_v6="::1",
            dynamic_range_v4_start="127.0.0.1",
            dynamic_range_v4_end="127.0.0.1",
            dynamic_range_v6_start="::1",
            dynamic_range_v6_end="::1",
        )
        architecture = Architecture.objects.get(name="x86_64")
        self.remotepowerdevice = RemotePowerDevice.objects.create(
            fqdn="rpower.orthos2.test",
            mac="AA:BB:CC:DD:EE:FF",
            fence_agent=self.remotepowertype,
            architecture=architecture,
            domain=domain,
        )
        self.other_remotepowerdevice = RemotePowerDevice.objects.create(
            fqdn="other-rpower.orthos2.test",
            mac="AA:BB:CC:DD:EE:00",
            fence_agent=self.other_remotepowertype,
            architecture=architecture,
            domain=domain,
        )

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse(
            "frontend:remotepowertype_devices",
            kwargs={"id": self.remotepowertype.pk},
        )
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:remotepowertype_devices",
            kwargs={"id": self.remotepowertype.pk},
        )
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_lists_only_devices_with_this_remotepowertype(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:remotepowertype_devices",
            kwargs={"id": self.remotepowertype.pk},
        )
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"rpower.orthos2.test" in response.content
        assert b"other-rpower.orthos2.test" not in response.content

    def test_nonexistent_remotepowertype_returns_404(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:remotepowertype_devices", kwargs={"id": 99999})
        response = self.client.get(url)
        assert response.status_code == 404


class RemotePowerTypeDevicesBmcHypervisorViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        ServerConfig.objects.create(key="domain.validendings", value="orthos2.test")
        Domain.objects.create(
            name="orthos2.test",
            ip_v4="127.0.0.1",
            ip_v6="::1",
            dynamic_range_v4_start="127.0.0.1",
            dynamic_range_v4_end="127.0.0.1",
            dynamic_range_v6_start="::1",
            dynamic_range_v6_end="::1",
        )

    def test_bmc_category_lists_machine_via_bmc(self) -> None:
        bmc_type = RemotePowerType.objects.create(name="AcmeBMCType", device="bmc")
        machine = Machine.objects.create(
            fqdn="bmc-host.orthos2.test",
            system=System.objects.get(name="BareMetal"),
            architecture=Architecture.objects.get(name="x86_64"),
        )
        BMC.objects.create(
            machine=machine,
            fqdn="bmc.orthos2.test",
            mac="AA:BB:CC:DD:EE:02",
            fence_agent=bmc_type,
        )

        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:remotepowertype_devices", kwargs={"id": bmc_type.pk})
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"bmc-host.orthos2.test" in response.content

    def test_hypervisor_category_lists_machine_via_remotepower(self) -> None:
        hypervisor_type = RemotePowerType.objects.create(
            name="AcmeHypervisorType", device="hypervisor"
        )
        host = Machine.objects.create(
            fqdn="host.orthos2.test",
            system=System.objects.get(name="BareMetal"),
            architecture=Architecture.objects.get(name="x86_64"),
        )
        vm = Machine.objects.create(
            fqdn="vm.orthos2.test",
            system=System.objects.get(name="VM KVM"),
            architecture=Architecture.objects.get(name="x86_64"),
            hypervisor=host,
        )
        RemotePower.objects.create(machine=vm, fence_agent=hypervisor_type)

        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:remotepowertype_devices", kwargs={"id": hypervisor_type.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"vm.orthos2.test" in response.content

    def test_bmc_category_devices_list_correct_when_architectures_and_systems_restricted(
        self,
    ) -> None:
        bmc_type = RemotePowerType.objects.create(name="AcmeBMCType", device="bmc")
        bmc_type.architectures.add(Architecture.objects.get(name="x86_64"))
        bmc_type.systems.add(System.objects.get(name="BareMetal"))
        machine = Machine.objects.create(
            fqdn="restricted-bmc-host.orthos2.test",
            system=System.objects.get(name="BareMetal"),
            architecture=Architecture.objects.get(name="x86_64"),
        )
        BMC.objects.create(
            machine=machine,
            fqdn="restricted-bmc.orthos2.test",
            mac="AA:BB:CC:DD:EE:12",
            fence_agent=bmc_type,
        )

        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:remotepowertype_devices", kwargs={"id": bmc_type.pk})
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"restricted-bmc-host.orthos2.test" in response.content


class NewRemotePowerTypeViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse("frontend:new_remotepowertype")
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:new_remotepowertype")
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_form(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:new_remotepowertype")
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_creates_remotepowertype(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse("frontend:new_remotepowertype")
        response = self.client.post(
            url,
            {"name": "AcmeRemotePowerType", "device": "bmc"},
        )
        assert response.status_code == 302
        assert RemotePowerType.objects.filter(name="AcmeRemotePowerType").exists()

    def test_regular_user_post_does_not_create_remotepowertype(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse("frontend:new_remotepowertype")
        response = self.client.post(
            url,
            {"name": "AcmeRemotePowerType", "device": "bmc"},
        )
        assert response.status_code == 403
        assert not RemotePowerType.objects.filter(name="AcmeRemotePowerType").exists()


class RemotePowerTypeDetailedEditViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.remotepowertype = RemotePowerType.objects.create(
            name="AcmeRemotePowerType"
        )

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse(
            "frontend:edit_remotepowertype", kwargs={"pk": self.remotepowertype.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:edit_remotepowertype", kwargs={"pk": self.remotepowertype.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_form(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:edit_remotepowertype", kwargs={"pk": self.remotepowertype.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_updates_remotepowertype(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:edit_remotepowertype", kwargs={"pk": self.remotepowertype.pk}
        )
        response = self.client.post(
            url,
            {"name": "AcmeRemotePowerType Renamed", "device": "bmc"},
        )
        assert response.status_code == 302
        self.remotepowertype.refresh_from_db()
        assert self.remotepowertype.name == "AcmeRemotePowerType Renamed"

    def test_regular_user_post_does_not_update_remotepowertype(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:edit_remotepowertype", kwargs={"pk": self.remotepowertype.pk}
        )
        response = self.client.post(
            url,
            {"name": "AcmeRemotePowerType Renamed", "device": "bmc"},
        )
        assert response.status_code == 403
        self.remotepowertype.refresh_from_db()
        assert self.remotepowertype.name == "AcmeRemotePowerType"


class DeleteRemotePowerTypeViewTest(TestCase):
    fixtures = ["orthos2/frontend/tests/user/fixtures/users.json"]

    def setUp(self) -> None:
        self.remotepowertype = RemotePowerType.objects.create(
            name="AcmeRemotePowerType"
        )

    def test_unauthenticated_get_redirects_to_login(self) -> None:
        url = reverse(
            "frontend:delete_remotepowertype", kwargs={"pk": self.remotepowertype.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 302
        assert "login" in response.url.lower()  # type: ignore[attr-defined]

    def test_regular_user_get_is_forbidden(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:delete_remotepowertype", kwargs={"pk": self.remotepowertype.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 403

    def test_superuser_get_shows_confirmation_page(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:delete_remotepowertype", kwargs={"pk": self.remotepowertype.pk}
        )
        response = self.client.get(url)
        assert response.status_code == 200

    def test_superuser_post_deletes_remotepowertype(self) -> None:
        self.client.force_login(User.objects.get(username="superuser"))
        url = reverse(
            "frontend:delete_remotepowertype", kwargs={"pk": self.remotepowertype.pk}
        )
        response = self.client.post(url)
        assert response.status_code == 302
        assert not RemotePowerType.objects.filter(pk=self.remotepowertype.pk).exists()

    def test_regular_user_post_does_not_delete_remotepowertype(self) -> None:
        self.client.force_login(User.objects.get(username="user"))
        url = reverse(
            "frontend:delete_remotepowertype", kwargs={"pk": self.remotepowertype.pk}
        )
        response = self.client.post(url)
        assert response.status_code == 403
        assert RemotePowerType.objects.filter(pk=self.remotepowertype.pk).exists()
