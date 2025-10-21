# install new OpenSSL
brew install openssl

# generate private key and enter pass phrase
openssl genrsa -des3 -out hd_ssl_private_key.pem 2048

# create certificate signing request, enter "*.example.com" as a "Common Name", leave "challenge password" blank
openssl req -new -sha256 -key hd_ssl_private_key.pem -out hd_ssl_server.csr

# generate self-signed certificate for 1 year
openssl req -x509 -sha256 -days 365 -key hd_ssl_private_key.pem -in hd_ssl_server.csr -out hd_ssl_server.pem

# validate the certificate
openssl req -in hd_ssl_server.csr -text -noout | grep -i "Signature.*SHA256" && echo "All is well" || echo "This certificate doesn't work in 2017! You must update OpenSSL to generate a widely-compatible certificate"