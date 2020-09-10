# Copyright (c) 2020 SUSE LLC
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

# Please submit bugfixes or comments via https://bugs.opensuse.org/

Name:           orthos2
Version:        0.1
Release:        0
Summary:        Machine administration
Url:            https://github.com/openSUSE/orthos2

Group:          Productivity/Networking/Boot/Servers
%{?systemd_ordering}

License:        GPL-2.0-or-later
Source:         orthos2-%{version}.tar.gz
BuildArch:      noarch

BuildRequires:  systemd-rpm-macros
BuildRequires:  python3-setuptools
BuildRequires:  python3-devel


Requires:  python3-Django
Requires:  python3-django-extensions
Requires:  python3-paramiko
Requires:  python3-djangorestframework
Requires:  python3-validators
Requires:  python3-netaddr
Requires:  nginx
Requires:  uwsgi
Requires:  uwsgi-python3



Provides: orthos2-%{version}-%{release}

%description
Orthos is the machine administration tool of the development network at SUSE. It is used for following tasks:

    getting the state of the machine
    overview about the hardware
    overview about the installed software (installations)
    reservation of the machines
    generating the DHCP configuration (via Cobbler)
    reboot the machines remotely
    managing remote (serial) consoles


%prep
%setup

%build
%py3_build


%install
%py3_install

#systemd
mkdir -p %{buildroot}%{_unitdir}
install orthos2_taskmanager.service %{buildroot}%{_unitdir}
install orthos2_server.service %{buildroot}%{_unitdir}
install orthos2_uwsgi.ini %{buildroot}%{python3_sitelib}/orthos
install uwsgi_params %{buildroot}%{python3_sitelib}/orthos
%pre
getent group orthos >/dev/null || groupadd -r orthos
getent passwd orthos >/dev/null || \
    useradd -r -g orthos -d /home/orthos -s /sbin/nologin \
    -c "Useful comment about the purpose of this account" orthos
%service_add_pre orthos2_server.service orthos2_taskmanager.service

%post
%service_add_post orthos2_server.service orthos2_taskmanager.service

%preun
%service_del_preun  orthos2_server.service orthos2_taskmanager.service

%postun
%service_del_postun  orthos2_server.service orthos2_taskmanager.service



%files  
%{python3_sitelib}/orthos2-*
%attr(-,orthos, orthos) %{python3_sitelib}/orthos2/
%attr(744, orthos, orthos)%{python3_sitelib}/orthos2/manage.py
%config(noreplace) %{_sysconfdir}/nginx/conf.d/orthos2_nginx.conf
%dir %{_sysconfdir}/nginx
%dir %{_sysconfdir}/nginx/conf.d
%_unitdir/orthos2_taskmanager.service
%_unitdir/orthos2_server.service