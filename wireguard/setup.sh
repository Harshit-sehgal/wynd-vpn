#!/bin/bash

# Generate Server Keys
echo "Generating Server Keys..."
SERVER_PRIVATE=$(wg genkey)
SERVER_PUBLIC=$(echo $SERVER_PRIVATE | wg pubkey)
echo "Server Private: $SERVER_PRIVATE"
echo "Server Public: $SERVER_PUBLIC"

# Generate Laptop Keys
echo -e "\nGenerating Laptop Keys..."
LAPTOP_PRIVATE=$(wg genkey)
LAPTOP_PUBLIC=$(echo $LAPTOP_PRIVATE | wg pubkey)
echo "Laptop Private: $LAPTOP_PRIVATE"
echo "Laptop Public: $LAPTOP_PUBLIC"

# Generate Phone Keys
echo -e "\nGenerating Phone Keys..."
PHONE_PRIVATE=$(wg genkey)
PHONE_PUBLIC=$(echo $PHONE_PRIVATE | wg pubkey)
echo "Phone Private: $PHONE_PRIVATE"
echo "Phone Public: $PHONE_PUBLIC"

# Create Server Config
cat > wg-server.conf << EOF
[Interface]
Address = 10.0.0.1/24
ListenPort = 51820
PrivateKey = $SERVER_PRIVATE

[Peer]
PublicKey = $LAPTOP_PUBLIC
AllowedIPs = 10.0.0.2/32
PersistentKeepalive = 25

[Peer]
PublicKey = $PHONE_PUBLIC
AllowedIPs = 10.0.0.3/32
PersistentKeepalive = 25
EOF

# Create Laptop Config
cat > wg-laptop.conf << EOF
[Interface]
Address = 10.0.0.2/24
PrivateKey = $LAPTOP_PRIVATE
DNS = 1.1.1.1

[Peer]
PublicKey = $SERVER_PUBLIC
Endpoint = 161.118.177.7:51820
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
EOF

# Create Phone Config
cat > wg-phone.conf << EOF
[Interface]
Address = 10.0.0.3/24
PrivateKey = $PHONE_PRIVATE
DNS = 1.1.1.1

[Peer]
PublicKey = $SERVER_PUBLIC
Endpoint = 161.118.177.7:51820
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
EOF

echo -e "\nConfigs created: wg-server.conf, wg-laptop.conf, wg-phone.conf"
echo "Install wg-server.conf on your server"
echo "Import wg-laptop.conf on your laptop"
echo "Import wg-phone.conf on your phone (use QR code or file)"