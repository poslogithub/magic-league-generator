PyInstaller --noconfirm --clean .\magic_league_generator.spec
New-Item dist\sealed_generator\card_image -ItemType Directory
New-Item dist\sealed_generator\set_data -ItemType Directory
Compress-Archive -Path dist\sealed_generator -DestinationPath sealed_generator.zip
