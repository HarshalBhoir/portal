<?php

include('xmlapi.php');
include('config.php');

// Session parameters
$xmlapi = new xmlapi(DOMAIN_NAME);
$xmlapi->set_port(SERVER_PORT); // the ssl port for cpanel


// Email parameters
$email          = $argv['1'];
$email_password = "gE1(Re@t|Ve";
$email_quota    = '0';
$email_domain   = 'customer.pivotino.com';

// cPanel Auth and calling API
$xmlapi->password_auth(CPANEL_USER, CPANEL_PASSWORD);
$xmlapi->set_output('json');
$xmlapi->set_debug(0);
$result = $xmlapi->api1_query(CPANEL_USER, "Email", "addpop", array(
    $email,
    $email_password,
    $email_quota,
    $email_domain
));
$result = json_decode($result);
print_r($result->event->result);
