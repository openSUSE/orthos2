import json
from unittest import mock

from django.contrib.auth.models import User
from django.urls import reverse  # type: ignore
from django_webtest import WebTest  # type: ignore

from orthos2.data.models import (
    BMC,
    Architecture,
    Machine,
    RemotePowerType,
    SerialConsole,
    SerialConsoleType,
    ServerConfig,
    System,
)
from orthos2.data.models.domain import Domain


class ChangeView(WebTest):

    fixtures = [
        "orthos2/data/fixtures/systems.json",
        "orthos2/frontend/tests/user/fixtures/users.json",
        "orthos2/data/fixtures/architectures.json",
    ]

    @mock.patch("orthos2.data.models.machine.is_dns_resolvable")
    def setUp(self, m_is_dns_resolvable: mock.MagicMock):
        m_is_dns_resolvable.return_value = True

        ServerConfig.objects.create(key="domain.validendings", value="bar.de")

        Domain(
            name="foo.bar.de",
            ip_v4="127.0.0.1",
            ip_v6="::1",
            dynamic_range_v4_start="127.0.0.1",
            dynamic_range_v4_end="127.0.0.1",
            dynamic_range_v6_start="::1",
            dynamic_range_v6_end="::1",
        ).save()

        m1 = Machine()
        m1.pk = 1
        m1.system = System.get_system_manager().get_by_natural_key("BareMetal")
        m1.fqdn = "machine1.foo.bar.de"
        m1.architecture_id = (
            Architecture.get_architecture_manager().get_by_natural_key("x86_64").id
        )

        m1.save()

        m2 = Machine()
        m2.pk = 2
        m2.administrative = True
        m2.system = System.get_system_manager().get_by_natural_key("BareMetal")
        m2.fqdn = "machine2.foo.bar.de"
        m2.architecture_id = (
            Architecture.get_architecture_manager().get_by_natural_key("x86_64").id
        )

        m2.save()

        ipmi_fence_agent = RemotePowerType.objects.create(
            name="ipmilanplus", device="bmc"
        )
        ipmi_console_type = SerialConsoleType.objects.create(
            name="IPMI",
            command=(
                "ipmitool -I lanplus -H {{ machine.bmc.fqdn }} "
                "-U {{ ipmi.user}} -P {{ ipmi.password }} sol activate"
            ),
            comment="IPMI",
        )

        BMC.objects.create(
            username="root",
            password="root",
            fqdn="testsys-sp.orthos2.test",
            mac="AA:BB:CC:DD:EE:FF",
            machine=m2,
            fence_agent=ipmi_fence_agent,
        )
        SerialConsole.objects.create(
            machine=m2,
            stype=ipmi_console_type,
            kernel_device="ttyS",
            kernel_device_num=1,
            baud_rate=115200,
        )

    def test_visible_fieldsets_non_administrative_systems(self) -> None:
        """Test for fieldsets."""
        # Act
        page = self.app.get(  # type: ignore
            reverse("admin:data_machine_change", args=["1"]), user="superuser"
        )

        # Assert
        self.assertContains(page, "VIRTUALIZATION")  # type: ignore

    def test_visible_inlines_non_administrative_systems(self) -> None:
        """Test for inlines."""
        # Act
        page = self.app.get(  # type: ignore
            reverse("admin:data_machine_change", args=["1"]), user="superuser"
        )

        # Assert
        self.assertContains(page, "Add another Serial Console")  # type: ignore
        self.assertContains(page, "Remote Power")  # type: ignore

    def test_visible_fieldsets_administrative_systems(self) -> None:
        """Test for fieldsets."""
        # Act
        page = self.app.get(  # type: ignore
            reverse("admin:data_machine_change", args=["2"]), user="superuser"
        )

        # Assert
        self.assertContains(page, "VIRTUALIZATION")  # type: ignore

    def test_visible_inlines_administrative_systems(self) -> None:
        """Test for inlines."""
        # Act
        page = self.app.get(  # type: ignore
            reverse("admin:data_machine_change", args=["2"]), user="superuser"
        )

        # Assert
        self.assertContains(page, "Add another Serial Console")  # type: ignore
        self.assertContains(page, "Remote Power")  # type: ignore

    def test_deactivate_sol_button_visible_for_ipmi_console(self) -> None:
        """The machine detail page should expose the SOL deactivate action for IPMI consoles."""

        page = self.app.get(  # type: ignore
            reverse("frontend:detail", args=["2"]), user="superuser"
        )

        self.assertContains(page, "Queue SOL Deactivation")  # type: ignore

    def test_deactivate_sol_button_hidden_without_serialconsole(self) -> None:
        """The machine detail page should not expose the SOL action if no serial console exists."""

        page = self.app.get(  # type: ignore
            reverse("frontend:detail", args=["1"]), user="superuser"
        )

        self.assertNotContains(page, "Queue SOL Deactivation")  # type: ignore

    @mock.patch("orthos2.frontend.views.ajax.Machine.deactivate_sol")
    def test_ajax_deactivate_sol(self, mocked_deactivate_sol: mock.MagicMock) -> None:
        """The AJAX endpoint should queue the machine action and return a success payload."""

        mocked_deactivate_sol.return_value = True
        self.client.force_login(User.objects.get(username="superuser"))

        response = self.client.post(reverse("frontend:ajax_deactivate_sol", args=["2"]))

        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)
        self.assertEqual(payload["cls"], "success")
        self.assertEqual(
            payload["message"],
            "SOL deactivation was queued and will run in the background.",
        )
        mocked_deactivate_sol.assert_called_once_with(user=mock.ANY)

    def test_ajax_deactivate_sol_rejects_get(self) -> None:
        """The SOL deactivation endpoint should reject GET requests."""

        page = self.app.get(  # type: ignore
            reverse("frontend:ajax_deactivate_sol", args=["2"]),
            user="superuser",
            expect_errors=True,
        )

        self.assertEqual(page.status_int, 405)  # type: ignore[attr-defined]
