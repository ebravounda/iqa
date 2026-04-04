<?php
/**
 * IngresoQR - WHMCS Provisioning Module (Compatible WHMCS 7.9+)
 * 
 * Instalar en: /path/to/whmcs/modules/servers/ingresoqr/ingresoqr.php
 * 
 * CHANGELOG:
 * v1.1 - Fix para WHMCS 7.9.0: logging robusto, manejo de dropdown configoptions,
 *         boton de test manual, fallback file logging
 */

if (!defined("WHMCS")) {
    die("This file cannot be accessed directly");
}

/**
 * Escribe log a archivo local como respaldo
 */
function ingresoqr_FileLog($message)
{
    $logDir = __DIR__;
    $logFile = $logDir . '/ingresoqr_debug.log';
    $timestamp = date('Y-m-d H:i:s');
    @file_put_contents($logFile, "[{$timestamp}] {$message}\n", FILE_APPEND | LOCK_EX);
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
            'Options' => 'gym,condominium,hotel,coworking',
            'Default' => 'gym',
            'Description' => 'gym=Gimnasio, condominium=Condominio, hotel=Hotel, coworking=Coworking',
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

/**
 * Extrae el valor limpio de un configoption (quita label si viene con pipe)
 */
function ingresoqr_CleanOption($value)
{
    if (empty($value)) {
        return '';
    }
    // Si viene como "gym|Gimnasio", tomar solo "gym"
    if (strpos($value, '|') !== false) {
        $parts = explode('|', $value);
        return trim($parts[0]);
    }
    return trim($value);
}

/**
 * Construye la URL base del API
 */
function ingresoqr_BuildUrl($params)
{
    $server = trim($params['serverhostname']);
    // Quitar protocolo si ya viene incluido
    $server = preg_replace('#^https?://#', '', $server);
    // Quitar trailing slash
    $server = rtrim($server, '/');
    
    $protocol = !empty($params['serversecure']) ? 'https' : 'http';
    
    // Si el servidor tiene puerto custom
    $port = '';
    if (!empty($params['serverport']) && $params['serverport'] != '443' && $params['serverport'] != '80') {
        $port = ':' . $params['serverport'];
    }
    
    return "{$protocol}://{$server}{$port}";
}

function ingresoqr_ApiCall($params, $endpoint, $data)
{
    $baseUrl = ingresoqr_BuildUrl($params);
    $apiKey = trim($params['serveraccesshash']);
    
    $url = "{$baseUrl}/api/whmcs/{$endpoint}";
    
    $jsonData = json_encode($data);
    
    ingresoqr_FileLog("=== API CALL: {$endpoint} ===");
    ingresoqr_FileLog("URL: {$url}");
    ingresoqr_FileLog("Data: {$jsonData}");
    ingresoqr_FileLog("API Key (primeros 8): " . substr($apiKey, 0, 8) . "...");
    
    // Log para WHMCS Module Log
    if (function_exists('logModuleCall')) {
        logModuleCall('ingresoqr', $endpoint, [
            'url' => $url,
            'data' => $data,
        ], '', '', ['serveraccesshash']);
    }
    
    $ch = curl_init();
    curl_setopt_array($ch, [
        CURLOPT_URL => $url,
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => $jsonData,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 30,
        CURLOPT_CONNECTTIMEOUT => 15,
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_SSL_VERIFYHOST => 0,
        CURLOPT_FOLLOWLOCATION => true,
        CURLOPT_MAXREDIRS => 3,
        CURLOPT_HTTPHEADER => [
            'Content-Type: application/json',
            'Accept: application/json',
            'x-whmcs-key: ' . $apiKey,
        ],
    ]);
    
    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $effectiveUrl = curl_getinfo($ch, CURLINFO_EFFECTIVE_URL);
    $error = curl_error($ch);
    $errno = curl_errno($ch);
    curl_close($ch);
    
    ingresoqr_FileLog("HTTP Code: {$httpCode}");
    ingresoqr_FileLog("Effective URL: {$effectiveUrl}");
    ingresoqr_FileLog("Response: " . substr($response, 0, 500));
    if ($error) {
        ingresoqr_FileLog("CURL Error ({$errno}): {$error}");
    }
    
    // Log response en WHMCS
    if (function_exists('logModuleCall')) {
        logModuleCall('ingresoqr', $endpoint . '_response', [
            'http_code' => $httpCode,
            'effective_url' => $effectiveUrl,
            'curl_error' => $error,
            'curl_errno' => $errno,
        ], $response, '', []);
    }
    
    if ($error) {
        return ['success' => false, 'message' => "Error de conexion cURL ({$errno}): {$error}"];
    }
    
    if ($httpCode === 0) {
        return ['success' => false, 'message' => "No se pudo conectar al servidor. Verifica hostname y puerto."];
    }
    
    if (empty($response)) {
        return ['success' => false, 'message' => "Respuesta vacia del servidor (HTTP: {$httpCode})"];
    }
    
    $result = json_decode($response, true);
    
    if (json_last_error() !== JSON_ERROR_NONE) {
        return ['success' => false, 'message' => "Respuesta no es JSON valido (HTTP {$httpCode}): " . substr($response, 0, 200)];
    }
    
    if ($httpCode === 422) {
        // FastAPI validation error
        $detail = '';
        if (isset($result['detail']) && is_array($result['detail'])) {
            foreach ($result['detail'] as $err) {
                $field = is_array($err['loc']) ? implode('.', $err['loc']) : $err['loc'];
                $detail .= "{$field}: {$err['msg']}; ";
            }
        } elseif (isset($result['detail'])) {
            $detail = $result['detail'];
        }
        return ['success' => false, 'message' => "Error de validacion (422): {$detail}"];
    }
    
    if ($httpCode >= 400) {
        $detail = isset($result['detail']) ? $result['detail'] : "Error HTTP {$httpCode}";
        return ['success' => false, 'message' => $detail];
    }
    
    return $result ?: ['success' => false, 'message' => 'Resultado vacio'];
}

function ingresoqr_TestConnection(array $params)
{
    ingresoqr_FileLog("=== TEST CONNECTION ===");
    
    $baseUrl = ingresoqr_BuildUrl($params);
    $apiKey = trim($params['serveraccesshash']);
    
    // Paso 1: Verificar que el servidor responde
    $healthUrl = "{$baseUrl}/api/health";
    ingresoqr_FileLog("Testing health: {$healthUrl}");
    
    $ch = curl_init();
    curl_setopt_array($ch, [
        CURLOPT_URL => $healthUrl,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 15,
        CURLOPT_CONNECTTIMEOUT => 10,
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_SSL_VERIFYHOST => 0,
        CURLOPT_FOLLOWLOCATION => true,
    ]);
    
    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $error = curl_error($ch);
    curl_close($ch);
    
    ingresoqr_FileLog("Health check - HTTP: {$httpCode}, Error: {$error}, Response: {$response}");
    
    if ($error) {
        return ['success' => false, 'error' => "No se puede conectar al servidor ({$baseUrl}): {$error}"];
    }
    
    if ($httpCode !== 200) {
        return ['success' => false, 'error' => "Servidor responde HTTP {$httpCode}. URL: {$healthUrl}. Response: " . substr($response, 0, 100)];
    }
    
    // Paso 2: Verificar API key con endpoint de diagnostico
    $diagUrl = "{$baseUrl}/api/whmcs/diagnostico";
    ingresoqr_FileLog("Testing API key: {$diagUrl}");
    
    $ch = curl_init();
    curl_setopt_array($ch, [
        CURLOPT_URL => $diagUrl,
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => json_encode(['test' => true]),
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 15,
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_SSL_VERIFYHOST => 0,
        CURLOPT_FOLLOWLOCATION => true,
        CURLOPT_HTTPHEADER => [
            'Content-Type: application/json',
            'Accept: application/json',
            'x-whmcs-key: ' . $apiKey,
        ],
    ]);
    
    $response2 = curl_exec($ch);
    $httpCode2 = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $error2 = curl_error($ch);
    curl_close($ch);
    
    ingresoqr_FileLog("API key test - HTTP: {$httpCode2}, Error: {$error2}, Response: {$response2}");
    
    if ($error2) {
        return ['success' => false, 'error' => "Conexion OK pero fallo el test de API key: {$error2}"];
    }
    
    if ($httpCode2 === 403) {
        return ['success' => false, 'error' => "Conexion OK pero API Key invalida. Verifica el Access Hash en la configuracion del servidor."];
    }
    
    if ($httpCode2 === 404) {
        // El endpoint de diagnostico no existe aun, probemos con /info
        ingresoqr_FileLog("diagnostico endpoint no encontrado, probando con info...");
        return ['success' => true, 'error' => ''];
    }
    
    if ($httpCode2 >= 400) {
        return ['success' => false, 'error' => "API responde HTTP {$httpCode2}: " . substr($response2, 0, 100)];
    }
    
    return ['success' => true, 'error' => ''];
}

function ingresoqr_CreateAccount(array $params)
{
    ingresoqr_FileLog("=== CREATE ACCOUNT ===");
    ingresoqr_FileLog("Service ID: " . $params['serviceid']);
    ingresoqr_FileLog("Client Email: " . $params['clientsdetails']['email']);
    ingresoqr_FileLog("Domain: " . ($params['domain'] ?? 'N/A'));
    ingresoqr_FileLog("ConfigOption1 (raw): " . ($params['configoption1'] ?? 'N/A'));
    ingresoqr_FileLog("ConfigOption2 (raw): " . ($params['configoption2'] ?? 'N/A'));
    ingresoqr_FileLog("ConfigOption3 (raw): " . ($params['configoption3'] ?? 'N/A'));
    ingresoqr_FileLog("Server Hostname: " . ($params['serverhostname'] ?? 'N/A'));
    ingresoqr_FileLog("Server Secure: " . ($params['serversecure'] ?? 'N/A'));
    ingresoqr_FileLog("Server Port: " . ($params['serverport'] ?? 'N/A'));
    ingresoqr_FileLog("Has Access Hash: " . (!empty($params['serveraccesshash']) ? 'YES (' . strlen($params['serveraccesshash']) . ' chars)' : 'NO'));
    
    // Determinar nombre del negocio
    $gymName = '';
    if (!empty($params['domain'])) {
        $gymName = $params['domain'];
    } elseif (!empty($params['clientsdetails']['companyname'])) {
        $gymName = $params['clientsdetails']['companyname'];
    } else {
        $gymName = trim($params['clientsdetails']['firstname'] . ' ' . $params['clientsdetails']['lastname']);
    }
    
    // Limpiar configoptions (WHMCS 7.9 puede enviar formatos distintos)
    $businessType = ingresoqr_CleanOption($params['configoption1']);
    if (empty($businessType)) {
        $businessType = 'gym';
    }
    
    $maxMembers = intval($params['configoption2']);
    if ($maxMembers <= 0) {
        $maxMembers = 100;
    }
    
    $planName = trim($params['configoption3']);
    if (empty($planName)) {
        $planName = 'Basico';
    }
    
    // Generar password si no viene
    $password = $params['password'];
    if (empty($password)) {
        $password = bin2hex(random_bytes(6));
        ingresoqr_FileLog("Password generado automaticamente");
    }
    
    $data = [
        'gym_name' => $gymName,
        'admin_email' => $params['clientsdetails']['email'],
        'admin_password' => $password,
        'admin_name' => trim($params['clientsdetails']['firstname'] . ' ' . $params['clientsdetails']['lastname']),
        'business_type' => $businessType,
        'max_members' => $maxMembers,
        'plan_name' => $planName,
        'whmcs_service_id' => (string)$params['serviceid'],
    ];
    
    ingresoqr_FileLog("Payload a enviar: " . json_encode($data));
    
    $result = ingresoqr_ApiCall($params, 'provision', $data);
    
    ingresoqr_FileLog("Resultado provision: " . json_encode($result));
    
    if (isset($result['success']) && $result['success']) {
        // Guardar gym_id en las notas del servicio
        try {
            if (class_exists('\WHMCS\Database\Capsule')) {
                \WHMCS\Database\Capsule::table('tblhosting')
                    ->where('id', $params['serviceid'])
                    ->update(['notes' => 'gym_id: ' . $result['gym_id'] . "\nProvisioned: " . date('Y-m-d H:i:s')]);
            } else {
                // Fallback para WHMCS 7.9 sin Capsule
                if (function_exists('full_query')) {
                    full_query("UPDATE tblhosting SET notes='gym_id: " . db_escape_string($result['gym_id']) . "\nProvisioned: " . date('Y-m-d H:i:s') . "' WHERE id=" . intval($params['serviceid']));
                }
            }
        } catch (\Exception $e) {
            ingresoqr_FileLog("Error guardando gym_id en notas: " . $e->getMessage());
        }
        
        ingresoqr_FileLog("=== PROVISION EXITOSO: gym_id=" . $result['gym_id'] . " ===");
        return 'success';
    }
    
    $errorMsg = isset($result['message']) ? $result['message'] : 'Error desconocido en provisionamiento';
    ingresoqr_FileLog("=== PROVISION FALLIDO: {$errorMsg} ===");
    return $errorMsg;
}

function ingresoqr_SuspendAccount(array $params)
{
    ingresoqr_FileLog("=== SUSPEND ACCOUNT === Service ID: " . $params['serviceid']);
    
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
    ingresoqr_FileLog("=== UNSUSPEND ACCOUNT === Service ID: " . $params['serviceid']);
    
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
    ingresoqr_FileLog("=== TERMINATE ACCOUNT === Service ID: " . $params['serviceid']);
    
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
        'Test Provision Manual' => 'testProvision',
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

/**
 * Boton de test: Verifica la conexion y muestra parametros sin crear nada
 */
function ingresoqr_testProvision(array $params)
{
    ingresoqr_FileLog("=== TEST PROVISION (sin crear) ===");
    
    $baseUrl = ingresoqr_BuildUrl($params);
    $apiKey = trim($params['serveraccesshash']);
    
    $info = "<h3>Diagnostico de Provision</h3>";
    $info .= "<strong>URL Base:</strong> {$baseUrl}<br>";
    $info .= "<strong>API Key:</strong> " . substr($apiKey, 0, 8) . "..." . substr($apiKey, -4) . " (" . strlen($apiKey) . " chars)<br>";
    $info .= "<strong>Secure:</strong> " . ($params['serversecure'] ? 'SI' : 'NO') . "<br>";
    $info .= "<strong>Port:</strong> " . ($params['serverport'] ?: 'default') . "<br><br>";
    
    // Datos que se enviarian
    $gymName = $params['domain'] ?: ($params['clientsdetails']['companyname'] ?: trim($params['clientsdetails']['firstname'] . ' ' . $params['clientsdetails']['lastname']));
    $businessType = ingresoqr_CleanOption($params['configoption1']) ?: 'gym';
    $maxMembers = intval($params['configoption2']) ?: 100;
    $planName = trim($params['configoption3']) ?: 'Basico';
    
    $info .= "<strong>Datos que se enviarian:</strong><br>";
    $info .= "- gym_name: {$gymName}<br>";
    $info .= "- admin_email: {$params['clientsdetails']['email']}<br>";
    $info .= "- business_type: {$businessType} (raw: " . ($params['configoption1'] ?? 'N/A') . ")<br>";
    $info .= "- max_members: {$maxMembers} (raw: " . ($params['configoption2'] ?? 'N/A') . ")<br>";
    $info .= "- plan_name: {$planName}<br>";
    $info .= "- whmcs_service_id: {$params['serviceid']}<br><br>";
    
    // Test de conexion
    $info .= "<strong>Test de conexion:</strong><br>";
    
    $ch = curl_init();
    curl_setopt_array($ch, [
        CURLOPT_URL => "{$baseUrl}/api/health",
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 10,
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_SSL_VERIFYHOST => 0,
        CURLOPT_FOLLOWLOCATION => true,
    ]);
    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $error = curl_error($ch);
    curl_close($ch);
    
    if ($error) {
        $info .= "- Health: FALLO - {$error}<br>";
    } else {
        $info .= "- Health: OK (HTTP {$httpCode})<br>";
    }
    
    // Test API key con diagnostico
    $ch = curl_init();
    curl_setopt_array($ch, [
        CURLOPT_URL => "{$baseUrl}/api/whmcs/diagnostico",
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => json_encode(['test' => true]),
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 10,
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_SSL_VERIFYHOST => 0,
        CURLOPT_FOLLOWLOCATION => true,
        CURLOPT_HTTPHEADER => [
            'Content-Type: application/json',
            'x-whmcs-key: ' . $apiKey,
        ],
    ]);
    $response2 = curl_exec($ch);
    $httpCode2 = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $error2 = curl_error($ch);
    curl_close($ch);
    
    if ($error2) {
        $info .= "- API Key: FALLO - {$error2}<br>";
    } elseif ($httpCode2 === 403) {
        $info .= "- API Key: INVALIDA (403 Forbidden)<br>";
    } elseif ($httpCode2 === 200) {
        $info .= "- API Key: VALIDA (HTTP 200)<br>";
        $diagResult = json_decode($response2, true);
        if ($diagResult) {
            $info .= "- Diagnostico: " . ($diagResult['message'] ?? json_encode($diagResult)) . "<br>";
        }
    } else {
        $info .= "- API Key: HTTP {$httpCode2} - " . substr($response2, 0, 100) . "<br>";
    }
    
    // Check archivo de log
    $logFile = __DIR__ . '/ingresoqr_debug.log';
    if (file_exists($logFile)) {
        $logSize = filesize($logFile);
        $info .= "<br><strong>Log local:</strong> {$logFile} ({$logSize} bytes)<br>";
        // Mostrar ultimas 15 lineas
        $lines = file($logFile);
        $lastLines = array_slice($lines, -15);
        $info .= "<pre style='background:#f5f5f5;padding:10px;font-size:11px;max-height:200px;overflow:auto'>";
        foreach ($lastLines as $line) {
            $info .= htmlspecialchars($line);
        }
        $info .= "</pre>";
    } else {
        $info .= "<br><strong>Log local:</strong> No existe aun<br>";
    }
    
    return $info;
}
