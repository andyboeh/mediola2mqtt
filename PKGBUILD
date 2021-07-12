pkgname=mediola2mqtt-git
pkgver=r18.7bfbad8
pkgrel=1
pkgdesc="Simple Mediola to MQTT bridge"
arch=('any')
url="https://github.com/andyboeh/mediola2mqtt"
license=('GPL')
depends=('python' 'python-paho-mqtt' 'python-requests')
install='mediola2mqtt.install'
source=('mediola2mqtt-git::git+https://github.com/andyboeh/mediola2mqtt.git'
        'mediola2mqtt.install'
        'mediola2mqtt.sysusers'
        'mediola2mqtt.service')
provides=('mediola2mqtt')
conflicts=('mediola2mqtt')
sha256sums=('SKIP'
            '7c7970ac8da7a38a9799b8bd9a447ae9b7703b58e11b5cb1fa0fd47a85ef1197'
            'dd8e862cf307b24c3333a62ffd81962082fa50e689c33882bff74ac79f04c5d1'
            '44ba0df6671771e28f0d58d8b188a4bf25449a88cbe2f27189da54c17043ac70')
backup=('opt/mediola2mqtt/mediola2mqtt.yaml')

pkgver() {
  cd "$pkgname"
  printf "r%s.%s" "$(git rev-list --count HEAD)" "$(git rev-parse --short HEAD)"
}

package() {
  cd "${pkgname}"
  install -d "${pkgdir}/opt/mediola2mqtt"
  cp mediola2mqtt.py "${pkgdir}/opt/mediola2mqtt/mediola2mqtt.py"
  install -Dm644 "${srcdir}/mediola2mqtt.service" "${pkgdir}/usr/lib/systemd/system/mediola2mqtt.service"
  install -Dm644 "${srcdir}/mediola2mqtt.sysusers" "${pkgdir}/usr/lib/sysusers.d/mediola2mqtt.conf"
  install -Dm644 mediola2mqtt.yaml.example "${pkgdir}/opt/mediola2mqtt/mediola2mqtt.yaml"
}
