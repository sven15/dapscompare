#
# spec file for package dapscompare
#
# Copyright (c) 2017 SUSE LINUX GmbH, Nuernberg, Germany.
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

# Please submit bugfixes or comments via http://bugs.opensuse.org/
#


Name:           dapscompare
Version:        0.2.1
Release:        0
Summary:        Detect Rendering Changes in Documentation Built with DAPS
License:        MIT
Group:          Productivity/Publishing/XML
Url:            https://github.com/openSUSE/dapscompare
Source0:        %{name}-%{version}.tar.bz2
#
BuildRequires:  python3-Pillow
BuildRequires:  python3-devel
BuildRequires:  python3-numpy
BuildRequires:  python3-qt4
BuildRequires:  python3-scipy
BuildRequires:  python3-setuptools
BuildRequires:  python3-tk
#
Requires:       daps
Requires:       python3
Requires:       python3-Pillow
Requires:       python3-numpy
Requires:       python3-qt4
Requires:       python3-scipy
Requires:       python3-tk
#
BuildRoot:      %{_tmppath}/%{name}-%{version}-build
BuildArch:      noarch

%description
dapscompare allows detecting rendering changes in documentation built using
DAPS. To do so, it allows creating a set of reference images and can then
compares those to images created later on.

%prep
%setup -q


%build
python3 setup.py build


%install
python3 setup.py install --prefix=%{_prefix} --root=%{buildroot}


%files
%defattr(-,root,root)
%doc LICENSE ChangeLog README*
%{_bindir}/%{name}

%{python3_sitelib}/%{name}/
%{python3_sitelib}/%{name}-%{version}-py%{py3_ver}.egg-info

%changelog
