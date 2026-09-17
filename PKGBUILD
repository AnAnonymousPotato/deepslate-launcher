# Maintainer: Anirudh <anirudh@example.com>
pkgname=deepslate-launcher-git
pkgver=1.0.0
pkgrel=1
pkgdesc="Modern Minecraft-themed Bedrock Launcher for Linux with Ore UI theme"
arch=('any')
url="https://github.com/your-username/deepslate"
license=('MIT')
depends=('bedrock-on-linux-bin' 'python' 'python-pyside6')
optdepends=(
    'mangohud: in-game HUD overlay'
    'mesa-utils: graphics debugging tools'
)
provides=('deepslate-launcher')
conflicts=('deepslate-launcher')
source=('deepslate::git+https://github.com/your-username/deepslate.git')
sha256sums=('SKIP')

package() {
    cd "$srcdir/deepslate"
    install -dm755 "$pkgdir/opt/deepslate"
    cp -r assets src deepslate "$pkgdir/opt/deepslate/"

    install -dm755 "$pkgdir/usr/bin"
    ln -s /opt/deepslate/deepslate "$pkgdir/usr/bin/deepslate"

    install -Dm644 data/deepslate.desktop "$pkgdir/usr/share/applications/deepslate.desktop"
    sed -i "s|Exec=.*|Exec=/usr/bin/deepslate %U|" "$pkgdir/usr/share/applications/deepslate.desktop"

    install -Dm644 data/deepslate.png "$pkgdir/usr/share/icons/hicolor/256x256/apps/deepslate.png"
}
