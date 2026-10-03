// --- PREMIUM CUTE ORB ROBOT ---
document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('dashboard-robot-container');
    if (!container) return;

    try {
        if (!window.THREE) throw new Error("Three.js not loaded");
        
        const scene = new THREE.Scene();
        const width = container.clientWidth || 300;
        const height = container.clientHeight || 400;

        const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
        camera.position.set(0, 1.2, 5.5); 

        const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setSize(width, height);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        container.appendChild(renderer.domElement);

        // --- LIGHTING ---
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        scene.add(ambientLight);

        const mainLight = new THREE.DirectionalLight(0xffffff, 1.2);
        mainLight.position.set(5, 10, 7);
        scene.add(mainLight);

        const rimLight = new THREE.PointLight(0x0ea5e9, 4, 10);
        rimLight.position.set(-3, 3, -3);
        scene.add(rimLight);

        const fillLight = new THREE.PointLight(0x9d00ff, 2, 10);
        fillLight.position.set(3, -1, 2);
        scene.add(fillLight);

        // --- ROBOT MODEL ---
        const robotGroup = new THREE.Group();
        
        // Materials
        const bodyMat = new THREE.MeshStandardMaterial({ color: 0xffffff, metalness: 0.1, roughness: 0.2 });
        const glassMat = new THREE.MeshStandardMaterial({ color: 0x050505, metalness: 0.8, roughness: 0.1 });
        const eyeMat = new THREE.MeshBasicMaterial({ color: 0x00f0ff });

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
        const coreLight = new THREE.Mesh(new THREE.SphereGeometry(0.15, 16, 16), eyeMat);
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

        // --- ANIMATION LOOP ---
        let time = 0;
        function animate() {
            requestAnimationFrame(animate);
            time += 0.016;

            // Idle floating
            robotGroup.position.y = Math.sin(time * 1.5) * 0.1;
            
            // Core pulse
            const pulse = (Math.sin(time * 3) + 1) / 2;
            eyeMat.color.setHSL(0.5 + pulse * 0.05, 1, 0.5 + pulse * 0.2);

            // Blinking
            if (Math.random() > 0.99) {
                eyeL.scale.y = 0.01;
                eyeR.scale.y = 0.01;
                setTimeout(() => {
                    eyeL.scale.y = 1;
                    eyeR.scale.y = 1;
                }, 150);
            }
            
            // Look around
            headGroup.rotation.y = Math.sin(time * 0.6) * 0.25;
            headGroup.rotation.x = Math.sin(time * 0.4) * 0.1;

            // Fluid arm movement (shaking / floating)
            armLGroup.rotation.z = Math.sin(time * 1.2) * 0.1 + 0.1;
            armLGroup.rotation.x = Math.sin(time * 0.8) * 0.1;

            armRGroup.rotation.z = Math.sin(time * 3) * 0.2 - 0.3; // Waving motion
            armRGroup.rotation.x = -0.4;
            
            // Subtle body tilt
            robotGroup.rotation.y = Math.sin(time * 0.3) * 0.1;
            robotGroup.rotation.z = Math.sin(time * 0.2) * 0.05;

            renderer.render(scene, camera);
        }
        animate();
    } catch(e) {
        console.error("Dashboard robot error:", e);
    }
});
