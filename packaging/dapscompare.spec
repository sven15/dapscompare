#
# spec file for package dapscompare
#
# Copyright (c) 2016 SUSE LINUX GmbH, Nuernberg, Germany.
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
Version:        0.1.0
Release:        0
Summary:        Detect Rendering Changes in Documentation Built with DAPS
License:        MIT
Group:          Productivity/Publishing/XML
Url:            https://github.com/sven15/dapscompare
Source0:        %{name}-%{version}.tar.bz2
BuildRoot:      %{_tmppath}/%{name}-%{version}-build
BuildArch:      noarch

BuildRequires:  python3-devel
Requires:       daps
Requires:       python3
Requires:       python3-numpy
Requires:       python3-Pillow
Requires:       python3-qt4
Requires:       python3-scipy
Requires:       python3-tk

%description
dapscompare allows detecting rendering changes in documentation built using
DAPS. To do so, it allows creating a set of reference images and can then
compares those to images created later on.

%prep
%setup -q -n %{name}-%{version}


%build
# empty..?

%install
mkdir -p %{buildroot}%{_datadir}/%{name}
cp -r * %{buildroot}%{_datadir}/%{name}
mkdir -p %{buildroot}%{_bindir}
(cd %{buildroot}%{_bindir};ln -sr %{buildroot}%{_datadir}/%{name}/%{name}.py %{name})

%files
%defattr(-,root,root)

%dir %{_datadir}/%{name}
%{_datadir}/%{name}/*
%_bindir/%{name}


%changelog
