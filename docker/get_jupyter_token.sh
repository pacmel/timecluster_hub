#Para obtener url si no va la contraseña del token
ip="127.0.0.1"
port=$(hostname | sed -e "s/.*-//")
nombre=$port".etsisi.upm.es"
puerto_original="8888"
puerto_final="8866"
docker compose logs jupyter | grep "token=" | tail -n 1 | sed -e "s/$ip/$nombre/" -e "s/$puerto_original/$puerto_final/" | sed "s/.*\(http\)/\1/"
