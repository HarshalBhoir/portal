<?php

include('xmlapi.php');
include('dns_config.php');

// Session parameters
$xmlapi = new xmlapi(DOMAIN_NAME);
$xmlapi->set_port(SERVER_PORT); // the ssl port for cpanel

// Email parameters
$name  = $argv[1];

// cPanel Auth and calling API
$xmlapi->password_auth(CPANEL_USER, CPANEL_PASSWORD);
$xmlapi->set_output('json');
$xmlapi->set_debug(0);
$result = $xmlapi->api2_query(CPANEL_USER, "ZoneEdit", "add_zone_record", array(
    'domain' => 'pivotino.com',
    'name' => $name,
    'type' => 'A',
    'address' => '103.17.211.80',
    'ttl' => '600',
    'class' => 'IN',
));
$result = json_decode($result);
//print_r($result->event);
//echo "$result";
//echo "FAILED? SUCCESS?";