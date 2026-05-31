@NonCPS
Map parseJsonSafe(String json) {
    def parsed = new groovy.json.JsonSlurper().parseText(json)
    if (parsed instanceof Map) return new HashMap(parsed)
    return parsed
}

pipeline {
    agent { label 'windows' }

    environment {
        RUTA_BASE = "${WORKSPACE}\\test_runner"
        RUTA_PYTHON = "python"
        URL_BACKEND = "http://localhost:5000"
    }

    parameters {
        string(name: 'TEST_SCRIPT', defaultValue: '', description: 'Contenido Gherkin (individual)')
        string(name: 'TEST_CASE_ID', defaultValue: '', description: 'ID del caso de prueba')
        string(name: 'TEST_CASE_IDS', defaultValue: '', description: 'JSON: [1,2,3] o CSV: 1,2,3')
        string(name: 'TEST_CYCLE_ID', defaultValue: '', description: 'ID del ciclo (opcional)')
        string(name: 'REQUEST_ID', defaultValue: '', description: 'ID de solicitud')
    }

    stages {
        stage('Preparar workspace') {
            steps {
                script {
                    echo "Ruta base: ${RUTA_BASE}"
                    def rutaEjecutor = "${RUTA_BASE}\\ejecutor.py"
                    if (!fileExists(rutaEjecutor)) {
                        error "ejecutor.py NO encontrado en ${rutaEjecutor}"
                    }
                    echo "ejecutor.py OK"
                }
            }
        }

        stage('Detectar modo') {
            steps {
                script {
                    if (params.TEST_CASE_IDS?.trim()) {
                        echo "Modo CICLO detectado: ${params.TEST_CASE_IDS}"
                    } else if (params.TEST_CASE_ID?.trim()) {
                        echo "Modo INDIVIDUAL detectado: ${params.TEST_CASE_ID}"
                    } else {
                        error "TEST_CASE_ID o TEST_CASE_IDS requerido"
                    }
                    echo "URL Backend: ${URL_BACKEND}"
                    echo "Ruta Python: ${RUTA_PYTHON}"
                }
            }
        }

        stage('Ejecutar tests') {
            steps {
                script {
                    def ejecutarTest = { idTest, contenidoGherkin ->
                        def timestamp = System.currentTimeMillis()
                        def nombreFeature = "test_${idTest}_${timestamp}.feature"
                        def rutaFeature = "${RUTA_BASE}\\features\\${nombreFeature}"

                        if (contenidoGherkin?.trim()) {
                            writeFile file: rutaFeature, text: contenidoGherkin
                        } else {
                            error "TEST_SCRIPT no proporcionado. Proporciona contenido Gherkin válido para ejecutar la prueba."
                        }

                        def cmd = "\"${RUTA_PYTHON}\" \"${RUTA_BASE}\\ejecutor.py\" \"${rutaFeature}\" ${idTest}"
                        echo "Ejecutando: ${cmd}"

                        bat(
                            label: "Ejecutar Test ${idTest}",
                            script: cmd,
                            returnStdout: true
                        ).trim()

                        echo "Salida:"
                        echo salida

                        def lineasJson = []
                        salida.readLines().each { linea ->
                            def l = linea.trim()
                            if (l.startsWith("{") && l.endsWith("}")) {
                                lineasJson << l
                            }
                        }

                        if (lineasJson.isEmpty()) {
                            error "No se detectó JSON válido. Salida: ${salida}"
                        }

                        echo "Se detectaron ${lineasJson.size()} resultado(s)"

                        lineasJson.each { linea ->
                            def jsonObj = parseJsonSafe(linea)
                            if (params.TEST_CYCLE_ID?.trim()) {
                                jsonObj['ciclo_prueba_id'] = params.TEST_CYCLE_ID
                            }
                            if (params.REQUEST_ID?.trim()) {
                                jsonObj['id_solicitud'] = params.REQUEST_ID
                            }

                            def cuerpo = groovy.json.JsonOutput.toJson(jsonObj)
                            def urlCallback = "${URL_BACKEND}/automatizacion/api/resultados/desde-jenkins/${idTest}"

                            echo "POST -> ${urlCallback}"
                            try {
                                httpRequest(
                                    httpMode: 'POST',
                                    url: urlCallback,
                                    contentType: 'APPLICATION_JSON',
                                    requestBody: cuerpo,
                                    validResponseCodes: "100:399",
                                    timeout: 30
                                )
                                echo "Resultado enviado"
                            } catch (err) {
                                echo "Error enviando resultado: ${err}"
                            }
                        }
                    }

                    if (params.TEST_CASE_IDS?.trim()) {
                        def ids = null
                        try {
                            ids = new groovy.json.JsonSlurper().parseText(params.TEST_CASE_IDS)
                        } catch (e) {
                            ids = params.TEST_CASE_IDS.split(",").collect { it.trim() }
                        }

                        ids.each { valor ->
                            ejecutarTest(valor.toString(), "")
                        }
                    } else {
                        ejecutarTest(params.TEST_CASE_ID, params.TEST_SCRIPT)
                    }
                }
            }
        }
    }

    post {
        always {
            echo "Pipeline finalizado"
        }
    }
}
