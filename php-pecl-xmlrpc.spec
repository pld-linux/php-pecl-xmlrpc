#
# Conditional build:
%bcond_without	tests		# build without tests

%define		rel		1
%define		subver	RC3
%define		php_name	php%{?php_suffix}
%define		modname	xmlrpc
Summary:	xmlrpc extension module for PHP
Summary(pl.UTF-8):	Moduł xmlrpc dla PHP
Name:		%{php_name}-pecl-%{modname}
Version:	1.0.0
Release:	1.%{subver}.%{rel}
License:	PHP 3.01
Group:		Development/Languages/PHP
# https://github.com/php/pecl-networking-xmlrpc
Source0:	https://github.com/php/pecl-networking-xmlrpc/archive/refs/tags/xmlrpc-%{version}%{subver}.tar.gz
# Source0-md5:	f361711d8cf03080412c9680aa65f021
URL:		https://www.php.net/manual/en/book.xmlrpc.php
%{?with_tests:BuildRequires:    %{php_name}-cli}
BuildRequires:	%{php_name}-devel >= 4:8.0.0
BuildRequires:	rpmbuild(macros) >= 1.666
BuildRequires:	xmlrpc-epi-devel >= 0.54.1
BuildRequires:	%{php_name}-cli
%if %{with tests}
BuildRequires:	%{php_name}-pcre
%endif
%{?requires_php_extension}
Provides:	php(xmlrpc) = %{version}
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%description
This is a dynamic shared object (DSO) for PHP that will add XMLRPC
support.

%description -l pl.UTF-8
Moduł PHP dodający obsługę XMLRPC.

%prep
%setup -qc
mv pecl-networking-%{modname}-*/* .

%{__sed} -i -e '/PHP_ADD_LIBRARY_WITH_PATH/s#xmlrpc,#xmlrpc-epi,#' config.m4

cat <<'EOF' > run-tests.sh
#!/bin/sh
export NO_INTERACTION=1 REPORT_EXIT_STATUS=1 MALLOC_CHECK_=2
exec %{__make} test \
	PHP_EXECUTABLE=%{__php} \
	PHP_TEST_SHARED_SYSTEM_EXTENSIONS="" \
	RUN_TESTS_SETTINGS="-q $*"
EOF
chmod +x run-tests.sh

xfail() {
	local t=$1
	test -f $t
	cat >> $t <<-EOF

	--XFAIL--
	Skip
	EOF
}

while read line; do
	t=${line##*\[}; t=${t%\]}
	xfail $t
done << 'EOF'
xmlrpc_encode() Simple test encode type double and String [tests/005.phpt]
Bug #40576 (double values are truncated to 6 decimal digits when encoding) [tests/bug40576_64bit.phpt]
Bug #45555 (Segfault with invalid non-string as register_introspection_callback) [tests/bug45555.phpt]
Bug #45556 (Return value from callback isn't freed) [tests/bug45556.phpt]
Bug #77242 (heap out of bounds read in xmlrpc_decode()) [tests/bug77242.phpt]
%ifarch %{ix86}
Bug #40576 (double values are truncated to 6 decimal digits when encoding) [tests/bug40576.phpt]
%endif
EOF

%build
export CPPFLAGS="%{rpmcppflags} -I%{_includedir}/xmlrpc-epi"

phpize
%configure \
	--with-xmlrpc=shared,/usr \

%{__make}

# simple module load test
%{__php} -n -q \
	-d extension_dir=modules \
	-d extension=%{modname}.so \
	-m > modules.log
grep %{modname} modules.log

%if %{with tests}
./run-tests.sh --show-diff
%endif

%install
rm -rf $RPM_BUILD_ROOT
%{__make} install \
	EXTENSION_DIR=%{php_extensiondir} \
	INSTALL_ROOT=$RPM_BUILD_ROOT

install -d $RPM_BUILD_ROOT%{php_sysconfdir}/conf.d
cat <<'EOF' > $RPM_BUILD_ROOT%{php_sysconfdir}/conf.d/%{modname}.ini
; Enable %{modname} extension module
extension=%{modname}.so
EOF

%clean
rm -rf $RPM_BUILD_ROOT

%post
%php_webserver_restart

%postun
if [ "$1" = 0 ]; then
	%php_webserver_restart
fi

%files
%defattr(644,root,root,755)
%doc CREDITS LICENSE
%config(noreplace) %verify(not md5 mtime size) %{php_sysconfdir}/conf.d/%{modname}.ini
%attr(755,root,root) %{php_extensiondir}/%{modname}.so
