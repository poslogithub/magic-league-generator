PyInstaller --noconfirm --clean .\magic_league_generator.spec
New-Item dist\sealed_generator\card_image -ItemType Directory
New-Item dist\sealed_generator\set_data -ItemType Directory
Remove-Item dist\sealed_generator.zip
Compress-Archive -Path dist\sealed_generator -DestinationPath dist\sealed_generator.zip
