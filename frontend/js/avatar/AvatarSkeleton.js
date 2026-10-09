class AvatarSkeleton {
    constructor(scene) {
        this.scene = scene;
        this.bones = {};
        
        // Materials
        this.skinMat = new THREE.MeshStandardMaterial({
            color: 0x1e293b,
            roughness: 0.35,
            metalness: 0.25
        });
        this.jointMat = new THREE.MeshStandardMaterial({
            color: 0x06b6d4,
            roughness: 0.2,
            metalness: 0.7,
            emissive: 0x0891b2,
            emissiveIntensity: 0.35
        });
        this.torsoMat = new THREE.MeshStandardMaterial({
            color: 0x0f172a,
            roughness: 0.5,
            metalness: 0.4
        });
        
        this.buildSkeleton();
    }

    buildSkeleton() {
        // Root node
        const root = new THREE.Group();
        root.position.set(0, -0.65, 0);
        this.scene.add(root);
        this.bones.root = root;

        // Chest (Faces +Z)
        const chestGeo = new THREE.CylinderGeometry(0.24, 0.17, 0.52, 16);
        const chest = new THREE.Mesh(chestGeo, this.torsoMat);
        chest.position.y = 0.5;
        root.add(chest);
        this.bones.chest = chest;

        // Neck
        const neckGeo = new THREE.CylinderGeometry(0.08, 0.09, 0.12, 12);
        const neck = new THREE.Mesh(neckGeo, this.skinMat);
        neck.position.y = 0.31;
        chest.add(neck);

        // Head
        const headGroup = new THREE.Group();
        headGroup.position.y = 0.16;
        neck.add(headGroup);
        this.bones.head = headGroup;

        const headGeo = new THREE.SphereGeometry(0.155, 20, 20);
        const headMesh = new THREE.Mesh(headGeo, this.skinMat);
        headMesh.scale.set(1.0, 1.22, 1.08);
        headGroup.add(headMesh);

        // Visor
        const visorGeo = new THREE.BoxGeometry(0.18, 0.048, 0.12);
        const visorMat = new THREE.MeshBasicMaterial({ color: 0x06b6d4 });
        const visor = new THREE.Mesh(visorGeo, visorMat);
        visor.position.set(0, 0.02, 0.135);
        headGroup.add(visor);

        // Build Arms
        this.buildArm('right', -1); // Avatar's right, -X
        this.buildArm('left', 1);   // Avatar's left, +X
    }

    buildArm(side, sideSign) {
        // sideSign: -1 for Right (Avatar Right), +1 for Left (Avatar Left)
        
        // Shoulder
        const shoulder = new THREE.Group();
        shoulder.position.set(sideSign * 0.28, 0.22, 0.0);
        this.bones.chest.add(shoulder);
        this.bones[side + 'Shoulder'] = shoulder;

        const shoulderJoint = new THREE.Mesh(new THREE.SphereGeometry(0.068, 12, 12), this.jointMat);
        shoulder.add(shoulderJoint);

        // Upper Arm
        const upperArm = new THREE.Group();
        shoulder.add(upperArm);
        this.bones[side + 'UpperArm'] = upperArm;
        
        const upperArmMesh = new THREE.Mesh(new THREE.CylinderGeometry(0.052, 0.046, 0.28, 12), this.skinMat);
        upperArmMesh.position.y = -0.14;
        upperArm.add(upperArmMesh);

        // Elbow
        const elbow = new THREE.Group();
        elbow.position.y = -0.28;
        upperArm.add(elbow);
        this.bones[side + 'Elbow'] = elbow;
        
        const elbowJoint = new THREE.Mesh(new THREE.SphereGeometry(0.052, 12, 12), this.jointMat);
        elbow.add(elbowJoint);

        // Forearm
        const forearm = new THREE.Group();
        elbow.add(forearm);
        this.bones[side + 'Forearm'] = forearm;
        
        const forearmMesh = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.04, 0.26, 12), this.skinMat);
        forearmMesh.position.y = -0.13;
        forearm.add(forearmMesh);

        // Wrist
        const wrist = new THREE.Group();
        wrist.position.y = -0.26;
        forearm.add(wrist);
        this.bones[side + 'Wrist'] = wrist;

        // Hand Palm
        const palm = new THREE.Mesh(new THREE.BoxGeometry(0.075, 0.088, 0.026), this.skinMat);
        palm.position.y = -0.044;
        wrist.add(palm);
        this.bones[side + 'Hand'] = palm;

        // Fingers
        const fingerConfigs = [
            { name: 'thumb', medialOffset: 0.038, y: -0.022, len: 0.045, isThumb: true },
            { name: 'index', medialOffset: 0.024, y: -0.085, len: 0.052, isThumb: false },
            { name: 'middle', medialOffset: 0.0, y: -0.090, len: 0.056, isThumb: false },
            { name: 'ring', medialOffset: -0.022, y: -0.085, len: 0.050, isThumb: false },
            { name: 'pinky', medialOffset: -0.036, y: -0.075, len: 0.042, isThumb: false }
        ];

        fingerConfigs.forEach(cfg => {
            const posX = -sideSign * cfg.medialOffset; // thumb is medial
            
            // Base knuckle (MCP)
            const mcp = new THREE.Group();
            mcp.position.set(posX, cfg.y, 0);
            wrist.add(mcp);
            
            const proxLen = cfg.len * 0.55;
            const proxMesh = new THREE.Mesh(new THREE.BoxGeometry(0.015, proxLen, 0.015), this.jointMat);
            proxMesh.position.y = -proxLen / 2;
            mcp.add(proxMesh);

            // PIP / IP
            const pip = new THREE.Group();
            pip.position.y = -proxLen;
            mcp.add(pip);
            
            const distLen = cfg.len * 0.45;
            const distMesh = new THREE.Mesh(new THREE.BoxGeometry(0.013, distLen, 0.013), this.skinMat);
            distMesh.position.y = -distLen / 2;
            pip.add(distMesh);

            // Store references
            const capitalName = cfg.name.charAt(0).toUpperCase() + cfg.name.slice(1);
            this.bones[`${side}${capitalName}MCP`] = mcp;
            this.bones[`${side}${capitalName}PIP`] = pip;
        });
    }

    getBone(name) {
        if (!this.bones[name]) {
            console.error(`[AvatarSkeleton] Missing bone: ${name}`);
        }
        return this.bones[name];
    }
}
