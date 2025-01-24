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

%{?sle15_python_module_pythons}

%if 0%{?suse_version} > 1600
%define pythons python3
%define python3_pkgversion python3
%else
%define python3_pkgversion python311
%endif

Name:           orthos2
Version:        1.4
Release:        0
Summary:        Machine administration
Url:            https://github.com/openSUSE/orthos2

Group:          Productivity/Networking/Boot/Servers
%{?systemd_ordering}

License:        GPL-2.0-or-later
Source:         orthos2-%{version}.tar.gz
%if 0%{?suse_version}
Source1:        orthos2.rpmlintrc
%endif
BuildArch:      noarch

BuildRequires:  fdupes
BuildRequires:  systemd-rpm-macros
# For /etc/nginx{,/conf.d} creation
BuildRequires:  nginx
BuildRequires:  %{python_module devel}
BuildRequires:  %{python_module setuptools}
# Required for python3-asgiref
BuildRequires:  %{python_module typing_extensions if %python-base < 3.8}
Requires(post): sudo
BuildRequires:  python-rpm-macros

Requires:  %{python3_pkgversion}-Django >= 4.2
Requires:  %{python3_pkgversion}-django-extensions
Requires:  %{python3_pkgversion}-django-auth-ldap
Requires:  %{python3_pkgversion}-djangorestframework
Requires:  %{python3_pkgversion}-netaddr
Requires:  %{python3_pkgversion}-paramiko
Requires:  %{python3_pkgversion}-psycopg2
Requires:  %{python3_pkgversion}-ldap
Requires:  %{python3_pkgversion}-validators
Requires:  %{python3_pkgversion}-gunicorn

# Needed to install /etc/logrotate.d/orthos2
Requires:  logrotate
Requires:  nginx
Requires:  ansible

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

%package docs
Summary:        HTML documentation for orthos2
BuildRequires:  %{python_module django >= 4.2}
BuildRequires:  %{python_module django-auth-ldap}
BuildRequires:  %{python_module django-extensions}
BuildRequires:  %{python_module paramiko}
BuildRequires:  %{python_module djangorestframework}
BuildRequires:  %{python_module validators}
BuildRequires:  %{python_module netaddr}
BuildRequires:  %{python_module ldap}
BuildRequires:  %{python_module sphinx_rtd_theme}
BuildRequires:  %{python_module Sphinx}

%define orthos_web_docs /srv/www/orthos2/docs

%description docs
HTML documentation that can be put into a web servers htdocs directory for publishing.

%prep
%autosetup

%build
%python_build
cd docs
make html


%install
%python_install

# docs
mkdir -p %{buildroot}%{orthos_web_docs}

# client is built via separate spec file to reduce build dependencies
rm %{buildroot}/usr/bin/orthos2

cp -r docs/_build/html/* %{buildroot}%{orthos_web_docs}
%fdupes %{buildroot}/%{orthos_web_docs}
%python_expand %fdupes %{buildroot}/%{$python_sitelib}/orthos2/

cp -r ansible %{buildroot}/usr/lib/orthos2/ansible

%pre
getent group orthos >/dev/null || groupadd -r orthos
getent passwd orthos >/dev/null || \
    useradd -r -g orthos -d /var/lib/orthos2 -s /bin/bash \
    -c "Useful comment about the purpose of this account" orthos
%service_add_pre orthos2.service orthos2_taskmanager.service

%post
%tmpfiles_create %{_tmpfilesdir}/%{name}.conf
%service_add_post orthos2.service orthos2_taskmanager.service

%preun
%service_del_preun  orthos2.service orthos2_taskmanager.service

%postun
%service_del_postun  orthos2.service orthos2_taskmanager.service


%files
%{python_sitelib}/orthos2-*
%{_unitdir}/orthos2_taskmanager.service
%{_unitdir}/orthos2.service
%{_tmpfilesdir}/orthos2.conf
%dir %{python_sitelib}/orthos2/
%{python_sitelib}/orthos2/*
%dir %{_sysconfdir}/orthos2
%config %{_sysconfdir}/orthos2/settings
%config %{_sysconfdir}/logrotate.d/orthos2
%config(noreplace) %{_sysconfdir}/nginx/conf.d/orthos2_nginx.conf
%dir /usr/lib/orthos2
%dir /usr/lib/orthos2/scripts
%dir /usr/share/orthos2
%dir /usr/share/orthos2/fixtures
/usr/share/orthos2/fixtures/*
/usr/lib/orthos2/*
%attr(755,orthos,orthos) %{_bindir}/orthos-admin
%attr(755,orthos,orthos) %dir /srv/www/orthos2
%ghost %dir /run/%{name}
%ghost %dir /run/%{name}/ansible
%ghost %dir /run/%{name}/ansible_lastrun
%ghost %dir /run/%{name}/ansible_archive
%attr(755,orthos,orthos) %dir /var/log/orthos2
%attr(775,orthos,orthos) %dir /var/lib/orthos2
%attr(775,orthos,orthos) %dir /var/lib/orthos2/archiv
%attr(775,orthos,orthos) %dir /var/lib/orthos2/orthos-vm-images
%attr(775,orthos,orthos) %dir /var/lib/orthos2/database
%attr(700,orthos,orthos) %dir /var/lib/orthos2/.ssh

# defattr(fileattr, user, group, dirattr)
# Add whole ansible directory with correct attr for dirs and files
# Always keep this at the end with defattr
%defattr(664, orthos, orthos, 775)
/usr/lib/orthos2/ansible

%files docs
%dir %{orthos_web_docs}
%{orthos_web_docs}/*

%changelog
* Tue Sep 15 00:26:20 UTC 2020 - Thomas Renninger <trenn@suse.de>
- First submissions
