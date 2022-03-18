PyInstaller --noconfirm --clean ".\magic_league_generator.spec"
Compress-Archive -Path dist\sealed_generator -DestinationPath sealed_generator.zip
