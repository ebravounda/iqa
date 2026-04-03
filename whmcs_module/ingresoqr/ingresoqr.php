<?php
/**
 * IngresoQR - WHMCS Provisioning Module
 * 
 * Instalar en: /path/to/whmcs/modules/servers/ingresoqr/ingresoqr.php
 * 
 * Configuracion en WHMCS:
 * 1. Setup > Products/Services > Servers > Add New Server
 *    - Name: IngresoQR API
 *    - Hostname: c.ingresoqr.com
 *    - Access Hash: (tu WHMCS_API_KEY)
 * 
 * 2. Setup > Products/Services > Products > Create/Edit Product
 *    - Module Settings > Module Name: ingresoqr
 *    - Configurar campos personalizados
 */

if (!defined("WHMCS")) {
    die("This file cannot be accessed directly");
}

function ingresoqr_MetaData()
{
    return [
        'DisplayName' => 'IngresoQR - Control de Acceso',
        'APIVersion' => '1.0',
        'RequiresServer' => true,
    ];
}

function ingresoqr_ConfigOptions()
{
    return [
        'business_type' => [
            'FriendlyName' => 'Tipo de Negocio',
            'Type' => 'dropdown',
            'Options' => 'gym|Gimnasio,condominium|Condominio,hotel|Hotel,coworking|Coworking',
            'Default' => 'gym',
        ],
        'max_members' => [
            'FriendlyName' => 'Max Socios/Residentes',
            'Type' => 'text',
            'Size' => '10',
            'Default' => '100',
        ],
        'plan_name' => [
            'FriendlyName' => 'Nombre del Plan',
            'Type' => 'text',
            'Size' => '25',
            'Default' => 'Basico',
        ],
    ];
}

function ingresoqr_ApiCall($params, $endpoint, $data)
{
    $server = $params['serverhostname'];
    $apiKey = $params['serveraccesshash'];
    $protocol = $params['serversecure'] ? 'https' : 'http';
    
    $url = "{$protocol}://{$server}/api/whmcs/{$endpoint}";
    
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, 30);
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Content-Type: application/json',
        'x-whmcs-key: ' . $apiKey,
    ]);
    
    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $error = curl_error($ch);
    curl_close($ch);
    
    if ($error) {
        return ['success' => false, 'message' => "Connection error: {$error}"];
    }
    
    $result = json_decode($response, true);
    
    if ($httpCode >= 400) {
        $detail = isset($result['detail']) ? $result['detail'] : "HTTP Error {$httpCode}";
        return ['success' => false, 'message' => $detail];
    }
    
    return $result ?: ['success' => false, 'message' => 'Invalid response'];
}

function ingresoqr_CreateAccount(array $params)
{
    $data = [
        'gym_name' => $params['domain'] ?: $params['clientsdetails']['companyname'] ?: $params['clientsdetails']['firstname'] . ' ' . $params['clientsdetails']['lastname'],
        'admin_email' => $params['clientsdetails']['email'],
        'admin_password' => $params['password'],
        'admin_name' => $params['clientsdetails']['firstname'] . ' ' . $params['clientsdetails']['lastname'],
        'business_type' => $params['configoption1'] ?: 'gym',
        'max_members' => intval($params['configoption2']) ?: 100,
        'plan_name' => $params['configoption3'] ?: 'Basico',
        'whmcs_service_id' => (string)$params['serviceid'],
    ];
    
    $result = ingresoqr_ApiCall($params, 'provision', $data);
    
    if (isset($result['success']) && $result['success']) {
        // Save gym_id in custom field for future reference
        try {
            \WHMCS\Database\Capsule::table('tblhosting')
                ->where('id', $params['serviceid'])
                ->update(['notes' => 'gym_id: ' . $result['gym_id']]);
        } catch (\Exception $e) {
            // Non-critical
        }
        return 'success';
    }
    
    return $result['message'] ?? 'Unknown error during provisioning';
}

function ingresoqr_SuspendAccount(array $params)
{
    $data = [
        'whmcs_service_id' => (string)$params['serviceid'],
        'admin_email' => $params['clientsdetails']['email'],
    ];
    
    $result = ingresoqr_ApiCall($params, 'suspend', $data);
    
    if (isset($result['success']) && $result['success']) {
        return 'success';
    }
    
    return $result['message'] ?? 'Unknown error during suspension';
}

function ingresoqr_UnsuspendAccount(array $params)
{
    $data = [
        'whmcs_service_id' => (string)$params['serviceid'],
        'admin_email' => $params['clientsdetails']['email'],
    ];
    
    $result = ingresoqr_ApiCall($params, 'unsuspend', $data);
    
    if (isset($result['success']) && $result['success']) {
        return 'success';
    }
    
    return $result['message'] ?? 'Unknown error during unsuspension';
}

function ingresoqr_TerminateAccount(array $params)
{
    $data = [
        'whmcs_service_id' => (string)$params['serviceid'],
        'admin_email' => $params['clientsdetails']['email'],
    ];
    
    $result = ingresoqr_ApiCall($params, 'terminate', $data);
    
    if (isset($result['success']) && $result['success']) {
        return 'success';
    }
    
    return $result['message'] ?? 'Unknown error during termination';
}

function ingresoqr_AdminCustomButtonArray()
{
    return [
        'Ver Info del Negocio' => 'info',
    ];
}

function ingresoqr_info(array $params)
{
    $data = [
        'whmcs_service_id' => (string)$params['serviceid'],
        'admin_email' => $params['clientsdetails']['email'],
    ];
    
    $result = ingresoqr_ApiCall($params, 'info', $data);
    
    if (isset($result['success']) && $result['success']) {
        $typeLabels = [
            'gym' => 'Gimnasio',
            'condominium' => 'Condominio',
            'hotel' => 'Hotel',
            'coworking' => 'Coworking',
        ];
        $type = $typeLabels[$result['business_type']] ?? $result['business_type'];
        $status = $result['status'] === 'active' ? 'Activo' : ucfirst($result['status']);
        
        return "<strong>Negocio:</strong> {$result['name']}<br>"
             . "<strong>Tipo:</strong> {$type}<br>"
             . "<strong>Estado:</strong> {$status}<br>"
             . "<strong>Socios Activos:</strong> {$result['active_members']}<br>"
             . "<strong>Total Socios:</strong> {$result['total_members']}<br>"
             . "<strong>Max Capacidad:</strong> " . ($result['max_members'] ?: 'Sin limite') . "<br>"
             . "<strong>Creado:</strong> {$result['created_at']}";
    }
    
    return $result['message'] ?? 'Could not retrieve info';
}
