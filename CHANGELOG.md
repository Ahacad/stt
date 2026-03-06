

### Bug Fixes

- Remove undefined WhisperModel type annotation ([8993d44](https://github.com/Ahacad/stt/commit/8993d44da7782ac36f04c8faac25cc5a3486e1e9))
- Focus target window before typing instead of --window flag ([8d09bfd](https://github.com/Ahacad/stt/commit/8d09bfdb9a15ae4bc25cc787cb71d6d5e27a7bc6))
- Use atomic xdotool chain with windowfocus for paste ([9c60dec](https://github.com/Ahacad/stt/commit/9c60dec0429b9bf15c54ff1947569cea7218edd7))
- Use windowactivate + type in single xdotool chain ([b7dc593](https://github.com/Ahacad/stt/commit/b7dc5934ec6e8c8562da9e9cc4f6ce4cf0b311b5))
- Split xdotool type and restore into separate calls ([b07ef19](https://github.com/Ahacad/stt/commit/b07ef19a02d214fe384cb0400e2189c494fed754))
- Use single ctrl+v paste instead of char-by-char typing ([680b592](https://github.com/Ahacad/stt/commit/680b5922944eee2af59cec7c4a7c9e99d7f72219))
- Disable BSPWM focus_follows_pointer during paste ([a88938d](https://github.com/Ahacad/stt/commit/a88938d87a4d06d7403cc6af2c35e77680e4e64c))
- Use xdotool type instead of ctrl+v paste ([2e0cc3a](https://github.com/Ahacad/stt/commit/2e0cc3abefbcd7984b2f4082d13fdfc749cfc416))
- Use ctrl+shift+v paste instead of xdotool type ([04dcb0e](https://github.com/Ahacad/stt/commit/04dcb0ef8b5b4b6982c85592480cc4df1064903c))

### Features

- Add one-command Windows build script ([2db3aa1](https://github.com/Ahacad/stt/commit/2db3aa19c4f98608b722ff7e7974269d33661918))
- Add hotkey capture dialog and config write-back ([77767c4](https://github.com/Ahacad/stt/commit/77767c4a61e29f1cccf59788f0e9bb85a1c166f0))
- Type into origin window and copy to clipboard ([4d08bbb](https://github.com/Ahacad/stt/commit/4d08bbb87d323ff0ceb25ca60f284d5baaa10a8b))
