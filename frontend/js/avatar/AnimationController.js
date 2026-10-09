class AvatarAnimationController {
    constructor(skeleton) {
        this.skeleton = skeleton;
        this.sequence = [];
        this.isPlaying = false;
        this.isPaused = false;
        this.playbackSpeed = 1.0;
        
        this.currentStepIndex = 0;
        this.stepStartTime = 0;
        this.stepDuration = 1.0;
        
        this.onStatusChange = null;
    }

    playSequence(plan) {
        if (!plan || !plan.sequence || plan.sequence.length === 0) {
            this.setStatus("No valid signs in sequence");
            return;
        }
        this.sequence = plan.sequence;
        this.currentStepIndex = 0;
        this.isPlaying = true;
        this.isPaused = false;
        this.prepareCurrentStep();
    }

    pause() {
        this.isPaused = true;
        this.setStatus("PAUSED");
    }

    resume() {
        if (this.isPlaying && this.isPaused) {
            this.isPaused = false;
            this.stepStartTime = performance.now();
        }
    }

    stop() {
        this.isPlaying = false;
        this.isPaused = false;
        this.currentStepIndex = 0;
        this.setStatus("IDLE (Stopped)");
        this.resetToIdle();
    }

    resetToIdle() {
        const idleArm = [0.0, 0.15, 0.0, 0.25, 0.0, 0.0];
        const idleHand = [0.2, 0.2, 0.2, 0.2, 0.2];
        this.applyPoseImmediate('left', idleArm, idleHand);
        this.applyPoseImmediate('right', idleArm, idleHand);
        this.skeleton.getBone('head').rotation.set(0, 0, 0);
    }

    setStatus(msg) {
        if (this.onStatusChange) this.onStatusChange(msg);
    }

    prepareCurrentStep() {
        if (this.currentStepIndex >= this.sequence.length) {
            this.isPlaying = false;
            this.setStatus("DONE SIGNING");
            setTimeout(() => {
                if (!this.isPlaying) this.setStatus("IDLE (Ready)");
            }, 2000);
            return;
        }

        const step = this.sequence[this.currentStepIndex];
        this.stepStartTime = performance.now();
        this.stepDuration = (step.duration || 1.0) / this.playbackSpeed;

        if (step.type === 'sign') {
            this.setStatus(`SIGNING: ${step.word}`);
        } else {
            this.setStatus(`SPELLING: ${step.word}`);
        }
    }

    applyPoseImmediate(side, armAngles, fingerCurls) {
        const pose = AvatarCoordinateAdapter.convertArmPose(side, armAngles);
        if (pose) {
            this.skeleton.getBone(side + 'Shoulder').quaternion.copy(pose.shoulderQuat);
            this.skeleton.getBone(side + 'Elbow').quaternion.copy(pose.elbowQuat);
            this.skeleton.getBone(side + 'Wrist').quaternion.copy(pose.wristQuat);
        }
        
        const handPose = AvatarCoordinateAdapter.convertHandPose(side, fingerCurls);
        if (handPose) {
            ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky'].forEach(f => {
                this.skeleton.getBone(side + f + 'MCP').quaternion.copy(handPose[f].mcpQuat);
                this.skeleton.getBone(side + f + 'PIP').quaternion.copy(handPose[f].pipQuat);
            });
        }
    }

    update(now) {
        if (!this.isPlaying || this.isPaused) return;

        const step = this.sequence[this.currentStepIndex];
        if (!step) {
            this.isPlaying = false;
            return;
        }

        const elapsed = (now - this.stepStartTime) / 1000;
        const progress = Math.min(1.0, elapsed / this.stepDuration);

        if (step.type === 'sign' && step.keyframes && step.keyframes.length > 0) {
            const kfs = step.keyframes;
            let kfA = kfs[0];
            let kfB = kfs[kfs.length - 1];

            for (let i = 0; i < kfs.length - 1; i++) {
                const tA = kfs[i].t / (step.duration || 1.0);
                const tB = kfs[i + 1].t / (step.duration || 1.0);
                if (progress >= tA && progress <= tB) {
                    kfA = kfs[i];
                    kfB = kfs[i + 1];
                    const localProgress = (progress - tA) / (tB - tA || 0.001);

                    // Interpolate semantic values then convert to quaternion
                    // Or convert to quaternion then SLERP. Since we have SLERP, let's SLERP quaternions for smoother rotation!
                    this.slerpArm('right', kfA, kfB, localProgress);
                    this.slerpArm('left', kfA, kfB, localProgress);

                    if (kfA.head && kfB.head) {
                        this.skeleton.getBone('head').rotation.x = kfA.head[0] + (kfB.head[0] - kfA.head[0]) * localProgress;
                    }
                    break;
                }
            }
        } else if (step.type === 'fingerspelling' && step.letters && step.letters.length > 0) {
            let accumulated = 0;
            let currentLetter = step.letters[0];
            for (const l of step.letters) {
                accumulated += (l.duration || 0.45) / this.playbackSpeed;
                if (elapsed <= accumulated) {
                    currentLetter = l;
                    break;
                }
            }

            if (currentLetter) {
                this.setStatus(`SPELLING: ${step.word} [${currentLetter.letter}]`);
                this.applyPoseImmediate('right', currentLetter.right_arm, currentLetter.right_hand);
            }
        }

        if (progress >= 1.0) {
            this.currentStepIndex++;
            this.prepareCurrentStep();
        }
    }

    slerpArm(side, kfA, kfB, localProgress) {
        const armKey = side + '_arm';
        const handKey = side + '_hand';
        if (kfA[armKey] && kfB[armKey]) {
            const poseA = AvatarCoordinateAdapter.convertArmPose(side, kfA[armKey]);
            const poseB = AvatarCoordinateAdapter.convertArmPose(side, kfB[armKey]);
            
            if (poseA && poseB) {
                this.skeleton.getBone(side + 'Shoulder').quaternion.copy(poseA.shoulderQuat).slerp(poseB.shoulderQuat, localProgress);
                this.skeleton.getBone(side + 'Elbow').quaternion.copy(poseA.elbowQuat).slerp(poseB.elbowQuat, localProgress);
                this.skeleton.getBone(side + 'Wrist').quaternion.copy(poseA.wristQuat).slerp(poseB.wristQuat, localProgress);
            }
        }
        
        if (kfA[handKey] || kfB[handKey]) {
            const hA = kfA[handKey] || [0,0,0,0,0];
            const hB = kfB[handKey] || [0,0,0,0,0];
            const pA = AvatarCoordinateAdapter.convertHandPose(side, hA);
            const pB = AvatarCoordinateAdapter.convertHandPose(side, hB);
            
            if (pA && pB) {
                ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky'].forEach(f => {
                    this.skeleton.getBone(side + f + 'MCP').quaternion.copy(pA[f].mcpQuat).slerp(pB[f].mcpQuat, localProgress);
                    this.skeleton.getBone(side + f + 'PIP').quaternion.copy(pA[f].pipQuat).slerp(pB[f].pipQuat, localProgress);
                });
            }
        }
    }
}
