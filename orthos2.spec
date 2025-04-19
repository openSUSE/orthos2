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
BuildRequires:  sysuser-tools

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
Requires:  %{python3_pkgversion}-terminado
Requires:  %{python3_pkgversion}-tornado

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

%package -n system-user-orthos
Summary:        Orthos user and group
Group:          System
%sysusers_requires

%description -n system-user-orthos
Orthos user and group required by orthos2 package

%prep
%autosetup

%build
%sysusers_generate_pre system-user-orthos.conf orthos system-user-orthos.conf
%python_build
cd docs
make html


%install
install -D -m 0644 system-user-orthos.conf %{buildroot}%{_sysusersdir}/system-user-orthos.conf
%python_install

# docs
mkdir -p %{buildroot}%{orthos_web_docs}

# client is built via separate spec file to reduce build dependencies
rm %{buildroot}%{_prefix}/bin/orthos2

cp -r docs/_build/html/* %{buildroot}%{orthos_web_docs}
%fdupes %{buildroot}/%{orthos_web_docs}
%python_expand %fdupes %{buildroot}/%{$python_sitelib}/orthos2/
%python_exec manage.py setup all --buildroot=%{buildroot}

%pre
%service_add_pre orthos2.service orthos2_taskmanager.service

%pre -n system-user-orthos -f orthos.pre

%post
%tmpfiles_create %{_tmpfilesdir}/%{name}.conf
%service_add_post orthos2.service orthos2_taskmanager.service

%preun
%service_del_preun  orthos2.service orthos2_taskmanager.service

%postun
%service_del_postun  orthos2.service orthos2_taskmanager.service


%files
%{python_sitelib}/%{name}-*
%{_unitdir}/%{name}_taskmanager.service
%{_unitdir}/%{name}.service
%{_tmpfilesdir}/orthos2.conf
%dir %{python_sitelib}/%{name}/
%{python_sitelib}/%{name}/*
%dir %{_sysconfdir}/%{name}
%config %{_sysconfdir}/%{name}/settings
%config %{_sysconfdir}/logrotate.d/%{name}
%config(noreplace) %{_sysconfdir}/nginx/conf.d/orthos2_nginx.conf
%dir %{_prefix}/lib/%{name}
%dir %{_prefix}/lib/%{name}/scripts
%{_prefix}/lib/%{name}/*
%attr(755,orthos,orthos) %{_bindir}/orthos-admin
%attr(755,orthos,orthos) %dir /srv/www/%{name}
%ghost %dir %{_rundir}/%{name}
%ghost %dir %{_rundir}/%{name}/ansible
%ghost %dir %{_rundir}/%{name}/ansible_lastrun
%ghost %dir %{_rundir}/%{name}/ansible_archive
%attr(755,orthos,orthos) %dir %{_localstatedir}/log/%{name}
%attr(775,orthos,orthos) %dir %{_sharedstatedir}/%{name}
%attr(775,orthos,orthos) %dir %{_sharedstatedir}/%{name}/archiv
%attr(775,orthos,orthos) %dir %{_sharedstatedir}/%{name}/orthos-vm-images
%attr(775,orthos,orthos) %dir %{_sharedstatedir}/%{name}/database
%attr(700,orthos,orthos) %dir %{_sharedstatedir}/%{name}/.ssh

# defattr(fileattr, user, group, dirattr)
# Add whole ansible directory with correct attr for dirs and files
# Always keep this at the end with defattr
%defattr(664, orthos, orthos, 775)
%{_prefix}/lib/%{name}/ansible

%files docs
%dir %{orthos_web_docs}
%{orthos_web_docs}/*

%files -n system-user-orthos
%{_sysusersdir}/system-user-orthos.conf

%changelog
* Tue Sep 15 00:26:20 UTC 2020 - Thomas Renninger <trenn@suse.de>
- First submissions
