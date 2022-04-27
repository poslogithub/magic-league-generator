Remove-Item "dist\sealed_generator.zip"
PyInstaller --noconfirm --clean ".\magic_league_generator.spec"
New-Item "dist\sealed_generator\card_image" -ItemType Directory
New-Item "dist\sealed_generator\set_data" -ItemType Directory
Copy-Item -Path "*.url" -Destination "dist"
Compress-Archive -Path "dist\*" -DestinationPath "dist\sealed_generator.zip"
