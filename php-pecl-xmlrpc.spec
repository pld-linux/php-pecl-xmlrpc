#
# Conditional build:
%bcond_without	tests		# build without tests

%define		rel		1
%define		commit	1ed83f2
%define		php_name	php%{?php_suffix}
%define		modname	xmlrpc
Summary:	xmlrpc extension module for PHP
Summary(pl.UTF-8):	Moduł xmlrpc dla PHP
Name:		%{php_name}-pecl-%{modname}
Version:	1.0.0
Release:	0.%{rel}.%{commit}
License:	PHP 3.01
Group:		Development/Languages/PHP
# http://git.php.net/?p=pecl/networking/xmlrpc.git
# https://github.com/php/pecl-networking-xmlrpc
Source0:	https://github.com/php/pecl-networking-xmlrpc/archive/%{commit}/php-pecl-%{modname}-%{version}-%{commit}.tar.gz
# Source0-md5:	db89c3183934c874f4a242e184439d5c
URL:		https://www.php.net/manual/en/book.xmlrpc.php
%{?with_tests:BuildRequires:    %{php_name}-cli}
BuildRequires:	%{php_name}-devel >= 4:8.0.0
BuildRequires:	rpmbuild(macros) >= 1.666
BuildRequires:	xmlrpc-epi-devel >= 0.54.1
%if %{with tests}
BuildRequires:	%{php_name}-cli
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
export NO_INTERACTION=1 REPORT_EXIT_STATUS=1 MALLOC_CHECK_=2
%{__make} test \
	PHP_EXECUTABLE=%{__php} \
	PHP_TEST_SHARED_SYSTEM_EXTENSIONS="" \
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
