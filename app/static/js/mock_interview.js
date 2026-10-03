document.addEventListener('DOMContentLoaded', () => {
    // --- UI ELEMENTS ---
    const startScreen = document.getElementById('startScreen');
    const questionScreen = document.getElementById('questionScreen');
    const startInterviewBtn = document.getElementById('startInterviewBtn');
    const nextQuestionBtn = document.getElementById('nextQuestionBtn');
    const finishInterviewBtn = document.getElementById('finishInterviewBtn');
    const endInterviewBtn = document.getElementById('endInterviewBtn');
    const speechBubble = document.getElementById('speechBubble');
    const speechText = document.getElementById('speechText');
    const interviewStatus = document.getElementById('interviewStatus');
    const statusIndicator = interviewStatus.querySelector('.status-indicator');
    const statusText = document.getElementById('statusText');
    const questionCounter = document.getElementById('questionCounter');
    const questionText = document.getElementById('questionText');
    const currentAnswerInput = document.getElementById('currentAnswerInput');
    const voiceBtn = document.getElementById('voiceBtn');
    const voiceStatus = document.getElementById('voiceStatus');
    const interviewForm = document.getElementById('interviewForm');
    
    let currentQuestionIndex = 0;
    const totalQuestions = window.INTERVIEW_QUESTIONS.length;
    let isInterviewActive = false;

    // --- THREE.JS SETUP ---
    const container = document.getElementById('canvas-container');
    let is3DActive = false;
    let setRobotState = function(state) {}; // Dummy function if 3D fails

    try {
        if (!window.THREE) throw new Error("Three.js not loaded from CDN");
        
        const scene = new THREE.Scene();
        
        // Fallback if clientWidth is 0
        const width = container.clientWidth || window.innerWidth;
        const height = container.clientHeight || window.innerHeight;

        const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
        camera.position.set(0, 1.5, 6);

        const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setSize(width, height);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        container.appendChild(renderer.domElement);
        
        console.log("Three.js initialized. Canvas size:", width, height);

        // --- LIGHTING ---
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        scene.add(ambientLight);

        const mainLight = new THREE.DirectionalLight(0xffffff, 0.8);
        mainLight.position.set(5, 10, 7);
        mainLight.castShadow = true;
        scene.add(mainLight);

        const rimLight = new THREE.PointLight(0x0ea5e9, 2, 10);
        rimLight.position.set(-3, 3, -3);
        scene.add(rimLight);

        const fillLight = new THREE.PointLight(0x4f46e5, 1, 10);
        fillLight.position.set(3, 1, 2);
        scene.add(fillLight);

        // --- ROBOT MODEL (Premium Cute Orb) ---
        const robotGroup = new THREE.Group();
        
        // Materials
        const bodyMat = new THREE.MeshStandardMaterial({ color: 0xffffff, metalness: 0.1, roughness: 0.2 });
        const glassMat = new THREE.MeshStandardMaterial({ color: 0x050505, metalness: 0.8, roughness: 0.1 });
        const eyeMat = new THREE.MeshBasicMaterial({ color: 0x06b6d4 });
        const coreMat = new THREE.MeshBasicMaterial({ color: 0x06b6d4 });

        // HEAD
        const headGroup = new THREE.Group();
        headGroup.position.y = 1.6;
        
        const head = new THREE.Mesh(new THREE.SphereGeometry(0.65, 32, 32), bodyMat);
        headGroup.add(head);

        // Faceplate (A cut-out sphere section rotated to the front)
        const visorGeo = new THREE.SphereGeometry(0.67, 32, 32, 0, Math.PI * 2, 0, Math.PI * 0.35);
        const visor = new THREE.Mesh(visorGeo, glassMat);
        visor.rotation.x = Math.PI / 2;
        headGroup.add(visor);

        // Eyes
        const eyeGeo = new THREE.CylinderGeometry(0.12, 0.12, 0.05, 16);
        const eyeL = new THREE.Mesh(eyeGeo, eyeMat);
        eyeL.rotation.x = Math.PI / 2;
        eyeL.position.set(-0.25, 0.1, 0.65);
        
        const eyeR = eyeL.clone();
        eyeR.position.set(0.25, 0.1, 0.65);
        
        headGroup.add(eyeL);
        headGroup.add(eyeR);

        // Cute Antenna
        const antStem = new THREE.Mesh(new THREE.CylinderGeometry(0.015, 0.015, 0.4), bodyMat);
        antStem.position.y = 0.8;
        const antBulb = new THREE.Mesh(new THREE.SphereGeometry(0.06), eyeMat);
        antBulb.position.y = 1.0;
        headGroup.add(antStem);
        headGroup.add(antBulb);

        robotGroup.add(headGroup);

        // BODY (Cute oval)
        const torsoGeo = new THREE.SphereGeometry(0.55, 32, 32);
        const torso = new THREE.Mesh(torsoGeo, bodyMat);
        torso.scale.y = 1.4;
        torso.position.y = 0.2;
        robotGroup.add(torso);

        // Core light
        const coreLight = new THREE.Mesh(new THREE.SphereGeometry(0.15, 16, 16), coreMat);
        coreLight.position.set(0, 0.4, 0.52);
        coreLight.scale.set(1.2, 0.8, 0.3);
        robotGroup.add(coreLight);

        // ARMS (Floating ovals like EVE)
        const armGeo = new THREE.SphereGeometry(0.12, 16, 16);
        
        const armLGroup = new THREE.Group();
        armLGroup.position.set(0.65, 0.7, 0);
        const armL = new THREE.Mesh(armGeo, bodyMat);
        armL.scale.y = 2.2;
        armL.position.y = -0.3;
        armLGroup.add(armL);
        robotGroup.add(armLGroup);

        const armRGroup = new THREE.Group();
        armRGroup.position.set(-0.65, 0.7, 0);
        const armR = new THREE.Mesh(armGeo, bodyMat);
        armR.scale.y = 2.2;
        armR.position.y = -0.3;
        armRGroup.add(armR);
        robotGroup.add(armRGroup);

        scene.add(robotGroup);

        let targetHeadRotation = { x: 0, y: 0 };
        let isMobile = window.innerWidth <= 768;

        window.addEventListener('resize', () => {
            isMobile = window.innerWidth <= 768;
            const w = container.clientWidth || window.innerWidth;
            const h = container.clientHeight || window.innerHeight;
            camera.aspect = w / h;
            camera.updateProjectionMatrix();
            renderer.setSize(w, h);
        });

        if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            container.addEventListener('mousemove', (e) => {
                if (isMobile) return;
                const rect = container.getBoundingClientRect();
                const mouseX = ((e.clientX - rect.left) / rect.width) * 2 - 1;
                const mouseY = -((e.clientY - rect.top) / rect.height) * 2 + 1;
                
                targetHeadRotation.y = mouseX * 0.5;
                targetHeadRotation.x = -mouseY * 0.3;
            });
        }

        let time = 0;
        function animate() {
            requestAnimationFrame(animate);
            time += 0.016;

            if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
                // Floating body
                robotGroup.position.y = Math.sin(time * 1.5) * 0.1;
                
                // Subtle body tilt
                robotGroup.rotation.y = Math.sin(time * 0.3) * 0.1;
                robotGroup.rotation.z = Math.sin(time * 0.2) * 0.05;

                const pulse = (Math.sin(time * 4) + 1) / 2;
                coreMat.opacity = 0.5 + (pulse * 0.5);
                
                if (isMobile) {
                    targetHeadRotation.y = Math.sin(time * 0.5) * 0.3;
                    targetHeadRotation.x = Math.sin(time * 0.3) * 0.1;
                }
                
                headGroup.rotation.y += (targetHeadRotation.y - headGroup.rotation.y) * 0.1;
                headGroup.rotation.x += (targetHeadRotation.x - headGroup.rotation.x) * 0.1;

                if (!isInterviewActive) {
                    // Waving when idle
                    armRGroup.rotation.z = Math.sin(time * 3) * 0.2 - 0.3;
                    armRGroup.rotation.x = -0.4;
                    armLGroup.rotation.z = Math.sin(time * 1.2) * 0.1 + 0.1;
                    armLGroup.rotation.x = Math.sin(time * 0.8) * 0.1;
                } else {
                    // Resting when interviewing
                    armRGroup.rotation.z += (0 - armRGroup.rotation.z) * 0.1;
                    armRGroup.rotation.x += (0 - armRGroup.rotation.x) * 0.1;
                    armLGroup.rotation.z += (0 - armLGroup.rotation.z) * 0.1;
                    armLGroup.rotation.x += (0 - armLGroup.rotation.x) * 0.1;
                }
                
                // Blinking
                if (Math.random() > 0.99) {
                    eyeL.scale.y = 0.01; eyeR.scale.y = 0.01;
                    setTimeout(() => { eyeL.scale.y = 1; eyeR.scale.y = 1; }, 150);
                }
            }
            renderer.render(scene, camera);
        }
        animate();
        
        // Setup state controller
        setRobotState = function(state) {
            if (state === 'LISTENING') {
                eyeMat.color.setHex(0xf59e0b);
                coreMat.color.setHex(0xf59e0b);
                speechText.innerText = "I'm listening...";
            } else if (state === 'IDLE') {
                eyeMat.color.setHex(0x06b6d4);
                coreMat.color.setHex(0x06b6d4);
                speechText.innerText = "Hi! I'm ready when you are.";
            } else if (state === 'THINKING') {
                speechText.innerText = "Let me think about that...";
            } else if (state === 'FINISHED') {
                eyeMat.color.setHex(0x10b981);
                coreMat.color.setHex(0x10b981);
                speechText.innerText = "Great job! Let's review your performance.";
            }
        };
        is3DActive = true;
        setRobotState('IDLE'); // Ensure it gets set
    } catch (e) {
        console.error("Failed to initialize 3D Mock Interview Room:", e);
        document.getElementById('speechText').innerText = "3D Error: " + e.message;
        
        // Fallback for state text even if 3D fails
        setRobotState = function(state) {
            if (state === 'LISTENING') speechText.innerText = "I'm listening...";
            else if (state === 'IDLE') speechText.innerText = "3D Error: " + e.message;
            else if (state === 'THINKING') speechText.innerText = "Let me think about that...";
            else if (state === 'FINISHED') speechText.innerText = "Great job! Let's review your performance.";
        };
    }

    function loadQuestion(index) {
        if (index >= totalQuestions) return;
        const q = window.INTERVIEW_QUESTIONS[index];
        questionCounter.innerText = `QUESTION ${index + 1} OF ${totalQuestions}`;
        questionText.innerText = q.text;
        
        // Restore existing answer if navigating (not implemented in this flow, but good practice)
        const hiddenInput = document.getElementById(`answer_${index + 1}`);
        currentAnswerInput.value = hiddenInput.value || '';
        currentAnswerInput.focus();

        if (index === totalQuestions - 1) {
            nextQuestionBtn.classList.add('d-none');
            finishInterviewBtn.classList.remove('d-none');
        } else {
            nextQuestionBtn.classList.remove('d-none');
            finishInterviewBtn.classList.add('d-none');
        }
    }

    startInterviewBtn.addEventListener('click', () => {
        isInterviewActive = true;
        startScreen.classList.add('d-none');
        questionScreen.classList.remove('d-none');
        
        statusIndicator.classList.remove('online');
        statusIndicator.classList.add('progress');
        statusText.innerText = "Interview in Progress";
        
        setRobotState('LISTENING');
        loadQuestion(0);
    });

    function saveCurrentAnswer() {
        const hiddenInput = document.getElementById(`answer_${currentQuestionIndex + 1}`);
        hiddenInput.value = currentAnswerInput.value;
    }

    nextQuestionBtn.addEventListener('click', () => {
        if (!currentAnswerInput.checkValidity()) {
            currentAnswerInput.reportValidity();
            return;
        }
        
        saveCurrentAnswer();
        setRobotState('THINKING');
        
        setTimeout(() => {
            currentQuestionIndex++;
            loadQuestion(currentQuestionIndex);
            currentAnswerInput.value = ''; // clear for next
            setRobotState('LISTENING');
        }, 1000);
    });

    const completionScreen = document.getElementById('completionScreen');
    const viewFeedbackBtn = document.getElementById('viewFeedbackBtn');

    interviewForm.addEventListener('submit', (e) => {
        e.preventDefault(); // Don't submit yet
        if (!currentAnswerInput.checkValidity()) {
            currentAnswerInput.reportValidity();
            return;
        }
        saveCurrentAnswer();
        setRobotState('FINISHED');
        
        questionScreen.classList.add('d-none');
        completionScreen.classList.remove('d-none');
        
        statusIndicator.classList.remove('progress');
        statusIndicator.classList.add('online');
        statusText.innerText = "Interview Completed";
    });

    viewFeedbackBtn.addEventListener('click', () => {
        viewFeedbackBtn.innerHTML = '<i class="spinner-border spinner-border-sm me-2"></i> Generating Feedback...';
        viewFeedbackBtn.disabled = true;
        interviewForm.submit(); // Now actually submit the form
    });

    endInterviewBtn.addEventListener('click', () => {
        if (confirm("Are you sure you want to end the interview early? Your progress will be lost.")) {
            isInterviewActive = false;
            questionScreen.classList.add('d-none');
            startScreen.classList.remove('d-none');
            
            statusIndicator.classList.remove('progress');
            statusIndicator.classList.add('online');
            statusText.innerText = "Interviewer Online";
            
            setRobotState('IDLE');
            currentQuestionIndex = 0;
            currentAnswerInput.value = '';
        }
    });

    // --- VOICE INPUT ---
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let recognition = null;
    let isRecording = false;

    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;

        recognition.onstart = () => {
            isRecording = true;
            voiceBtn.classList.add('recording');
            voiceStatus.classList.remove('d-none');
            voiceBtn.innerHTML = '<i class="bi bi-stop-fill"></i>';
        };

        recognition.onresult = (event) => {
            let interimTranscript = '';
            let finalTranscript = '';

            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    finalTranscript += event.results[i][0].transcript;
                } else {
                    interimTranscript += event.results[i][0].transcript;
                }
            }
            
            // Append final safely, or just update value if not editing manually
            if (finalTranscript) {
                currentAnswerInput.value += (currentAnswerInput.value ? ' ' : '') + finalTranscript;
            }
        };

        recognition.onerror = (event) => {
            console.error('Speech recognition error', event.error);
            stopRecording();
        };

        recognition.onend = () => {
            stopRecording();
        };
    } else {
        voiceBtn.style.display = 'none';
    }

    function stopRecording() {
        if (isRecording && recognition) {
            recognition.stop();
            isRecording = false;
            voiceBtn.classList.remove('recording');
            voiceStatus.classList.add('d-none');
            voiceBtn.innerHTML = '<i class="bi bi-mic-fill"></i>';
        }
    }

    voiceBtn.addEventListener('click', () => {
        if (!recognition) return;
        
        if (isRecording) {
            stopRecording();
        } else {
            recognition.start();
        }
    });
});
