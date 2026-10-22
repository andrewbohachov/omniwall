# Maintainer: OmniWall Developers <chelsea@local>
pkgname=omniwall
pkgver=1.0.0
pkgrel=1
pkgdesc="Cross-Desktop 4K Wallpaper Rotator for Linux (KDE, GNOME, XFCE, Wayland)"
arch=('any')
url="https://github.com/andrewbohachov/omniwall"
license=('MIT')
depends=('python')
optdepends=(
    'plasma-workspace: for KDE Plasma support'
    'libglib2.0-bin: for GNOME gsettings support'
    'swww: for Wayland compositors (Hyprland, Sway)'
    'feh: for generic X11 window managers'
    'libnotify: for desktop notifications'
)
source=("$pkgname-$pkgver.tar.gz::$url/archive/refs/tags/v$pkgver.tar.gz")
sha256sums=('SKIP')

package() {
    cd "$srcdir/$pkgname-$pkgver"
    install -Dm755 omniwall.py "$pkgdir/usr/bin/omniwall"
    ln -sf omniwall "$pkgdir/usr/bin/wallpapers"
    ln -sf omniwall "$pkgdir/usr/bin/grimwall"
    
    install -Dm644 systemd/omniwall.service "$pkgdir/usr/lib/systemd/user/omniwall.service"
    install -Dm644 systemd/omniwall.timer "$pkgdir/usr/lib/systemd/user/omniwall.timer"
    install -Dm644 config.default.json "$pkgdir/etc/omniwall/config.json"
}
