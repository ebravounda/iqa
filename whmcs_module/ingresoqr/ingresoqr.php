<?php
/**
 * IngresoQR - WHMCS Provisioning Module (Compatible WHMCS 7.9+)
 * 
 * Instalar en: /path/to/whmcs/modules/servers/ingresoqr/ingresoqr.php
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
    $protocol = !empty($params['serversecure']) ? 'https' : 'http';
    
    $url = "{$protocol}://{$server}/api/whmcs/{$endpoint}";
    
    // Log para debug
    logModuleCall('ingresoqr', $endpoint, [
        'url' => $url,
        'data' => $data,
    ], '', '', []);
    
    $ch = curl_init();
    curl_setopt_array($ch, [
        CURLOPT_URL => $url,
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => json_encode($data),
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 30,
        CURLOPT_CONNECTTIMEOUT => 10,
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_SSL_VERIFYHOST => 0,
        CURLOPT_FOLLOWLOCATION => true,
        CURLOPT_HTTPHEADER => [
            'Content-Type: application/json',
            'Accept: application/json',
            'x-whmcs-key: ' . trim($apiKey),
        ],
    ]);
    
    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $error = curl_error($ch);
    $errno = curl_errno($ch);
    curl_close($ch);
    
    // Log response
    logModuleCall('ingresoqr', $endpoint . '_response', [
        'http_code' => $httpCode,
        'curl_error' => $error,
        'curl_errno' => $errno,
    ], $response, '', []);
    
    if ($error) {
        return ['success' => false, 'message' => "Curl error ({$errno}): {$error}"];
    }
    
    if (empty($response)) {
        return ['success' => false, 'message' => "Empty response from server (HTTP: {$httpCode})"];
    }
    
    $result = json_decode($response, true);
    
    if (json_last_error() !== JSON_ERROR_NONE) {
        return ['success' => false, 'message' => "Invalid JSON response: " . substr($response, 0, 200)];
    }
    
    if ($httpCode >= 400) {
        $detail = isset($result['detail']) ? $result['detail'] : "HTTP Error {$httpCode}";
        return ['success' => false, 'message' => $detail];
    }
    
    return $result ?: ['success' => false, 'message' => 'Empty result'];
}

function ingresoqr_TestConnection(array $params)
{
    $server = $params['serverhostname'];
    $apiKey = $params['serveraccesshash'];
    $protocol = !empty($params['serversecure']) ? 'https' : 'http';
    
    $url = "{$protocol}://{$server}/api/health";
    
    $ch = curl_init();
    curl_setopt_array($ch, [
        CURLOPT_URL => $url,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 10,
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_SSL_VERIFYHOST => 0,
    ]);
    
    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $error = curl_error($ch);
    curl_close($ch);
    
    if ($error) {
        return ['success' => false, 'error' => "No se puede conectar: {$error}"];
    }
    
    if ($httpCode !== 200) {
        return ['success' => false, 'error' => "API responde HTTP {$httpCode}"];
    }
    
    // Test API key
    $testUrl = "{$protocol}://{$server}/api/whmcs/info";
    $ch = curl_init();
    curl_setopt_array($ch, [
        CURLOPT_URL => $testUrl,
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => json_encode(['whmcs_service_id' => 'test']),
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 10,
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_SSL_VERIFYHOST => 0,
        CURLOPT_HTTPHEADER => [
            'Content-Type: application/json',
            'x-whmcs-key: ' . trim($apiKey),
        ],
    ]);
    
    $response2 = curl_exec($ch);
    $httpCode2 = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    
    if ($httpCode2 === 403) {
        return ['success' => false, 'error' => "API Key invalida. Verifica el Access Hash."];
    }
    
    return ['success' => true, 'error' => ''];
}

function ingresoqr_CreateAccount(array $params)
{
    $gymName = '';
    if (!empty($params['domain'])) {
        $gymName = $params['domain'];
    } elseif (!empty($params['clientsdetails']['companyname'])) {
        $gymName = $params['clientsdetails']['companyname'];
    } else {
        $gymName = $params['clientsdetails']['firstname'] . ' ' . $params['clientsdetails']['lastname'];
    }
    
    $data = [
        'gym_name' => $gymName,
        'admin_email' => $params['clientsdetails']['email'],
        'admin_password' => $params['password'] ?: bin2hex(random_bytes(6)),
        'admin_name' => $params['clientsdetails']['firstname'] . ' ' . $params['clientsdetails']['lastname'],
        'business_type' => $params['configoption1'] ?: 'gym',
        'max_members' => intval($params['configoption2']) ?: 100,
        'plan_name' => $params['configoption3'] ?: 'Basico',
        'whmcs_service_id' => (string)$params['serviceid'],
    ];
    
    $result = ingresoqr_ApiCall($params, 'provision', $data);
    
    if (isset($result['success']) && $result['success']) {
        try {
            if (class_exists('\WHMCS\Database\Capsule')) {
                \WHMCS\Database\Capsule::table('tblhosting')
                    ->where('id', $params['serviceid'])
                    ->update(['notes' => 'gym_id: ' . $result['gym_id']]);
            } else {
                full_query("UPDATE tblhosting SET notes='gym_id: " . db_escape_string($result['gym_id']) . "' WHERE id=" . intval($params['serviceid']));
            }
        } catch (\Exception $e) {
            // Non-critical
        }
        return 'success';
    }
    
    return isset($result['message']) ? $result['message'] : 'Error desconocido en provisionamiento';
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
    
    return isset($result['message']) ? $result['message'] : 'Error en suspension';
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
    
    return isset($result['message']) ? $result['message'] : 'Error en reactivacion';
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
    
    return isset($result['message']) ? $result['message'] : 'Error en terminacion';
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
        $type = isset($typeLabels[$result['business_type']]) ? $typeLabels[$result['business_type']] : $result['business_type'];
        $status = $result['status'] === 'active' ? 'Activo' : ucfirst($result['status']);
        
        return "<strong>Negocio:</strong> {$result['name']}<br>"
             . "<strong>Tipo:</strong> {$type}<br>"
             . "<strong>Estado:</strong> {$status}<br>"
             . "<strong>Socios Activos:</strong> {$result['active_members']}<br>"
             . "<strong>Total Socios:</strong> {$result['total_members']}<br>"
             . "<strong>Max Capacidad:</strong> " . ($result['max_members'] ?: 'Sin limite') . "<br>"
             . "<strong>Creado:</strong> {$result['created_at']}";
    }
    
    return isset($result['message']) ? $result['message'] : 'No se pudo obtener info';
}
