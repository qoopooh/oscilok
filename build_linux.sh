#!/bin/bash
# 
# dpkg -l | grep python-sample
# time sudo dpkg -i python-sample-deb.deb
# time sudo dpkg -P python-sample-deb
#
# rpm -qa | grep python-sample
# time sudo rpm -vi python-sample-rpm.rpm
# time sudo rpm -ve python-sample-rpm
#

VERSION=$(grep -E 'VERSION = "(.*)"' src/main.pyw | awk '{print $3}' | tr -d '"')
PACKAGE_TYPE=("deb" "rpm")
PACK=$1

if [[ -z "$PACK" ]]; then
  PACK=deb
fi
if [[ ! "${PACKAGE_TYPE[*]}" =~ "$PACK" ]]; then
  echo "Please assign package type: ${PACKAGE_TYPE[@]}"
  exit
fi

if ! command -v fpm &> /dev/null; then
  echo "Please install 'fpm':"
  echo " $ sudo apt install ruby"
  echo " $ gem install fpm --user-install"
  exit
fi

echo "Create oscilok-$VERSION.$PACK"

rm -rf build/ dist/ package/ oscilok.$PACK oscilok-$VERSION.$PACK && pyinstaller --name oscilok --windowed src/main.pyw --add-data="img/:img" --noconfirm

mkdir -p package/opt
mkdir -p package/usr/share/applications
mkdir -p package/usr/share/icons/hicolor/scalable/apps

cp -r dist/oscilok package/opt/oscilok
cp img/energy-green-panel-svgrepo-com.svg package/usr/share/icons/hicolor/scalable/apps/oscilok.svg
cp oscilok.desktop package/usr/share/applications/

find package/opt/oscilok -type f -exec chmod 644 -- {} +
find package/opt/oscilok -type d -exec chmod 755 -- {} +
find package/usr/share -type f -exec chmod 644 -- {} +
chmod +x package/opt/oscilok/oscilok

fpm -C package -s dir -t $PACK -n "oscilok" -v $VERSION -p oscilok.$PACK --rpm-rpmbuild-define "_build_id_links none"
mv oscilok.$PACK oscilok-$VERSION.$PACK
