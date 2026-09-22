# Current-runtime candidate selection and battle entry

This is a QA-only Web export. It does not change the production roster.

- QA URL: `http://127.0.0.1:8787/`
- QA PCK SHA256: `0921bd93f91b587c91391f4961f5ca93fecd1ae4182ddc3b9ccb227c43f82cc9`
- Runtime: `main.gd` `8ef3f927c78426fbd50b2ed700544aff1b31d2727f59adf018a357a900ca8c7d`; `helper_runtime.gd` `4a0f08ff087a498e9b15ed37bc166e2af9580ed4aa6b8e7853eaf742ce4f94f7`; `fighter_runtime.gd` `feb1a03f8a79ef9b9a0e1521d59b4ee57adb7501414c5856cb2c6ded4aefe5ac`.
- Availability override SHA256: `65cb4dd469d3e57976962df6cdd3e78a412c468bd3d32aef32707439db094173`.
- Mode: the captured mode screen showed `Vs Human` selected.
- Selection: P1 Byakuya was confirmed with `J`; P2 was moved with ArrowRight and confirmed at the Lee target with physical Numpad1 (`key=1`, `code=Numpad1`, `keyCode=97`, `which=97`, `location=3`).
- Helper/map: P1 helper, P2 helper, and map confirmation were sent in one continuous page session.
- Battle: `11-battle-hud.png` is a current-runtime visual entry proof showing both fighters and HUD. It is not a full action or source-parity verdict.
- Browser diagnostic run id: `ca50ff44-a8c2-4d46-b014-f723b88fdcf9`.

The console state was only available through the page's diagnostics context; the raw console event stream was not recovered in this run. Do not describe this artifact as raw COMBAT_EVENT evidence.

Action probe (same battle session): screenshots `12-p1-j.png`, `13-p2-n5.png`, `14-p2-n6.png` were taken after separate 350ms DOM key holds. The HUD energy remained `0` in these frames, so I/O/N5 cannot be classified as a positive special-action result under the required energy precondition. These images are visual observations only; no raw COMBAT_EVENT stream was recovered.

Pause menu probe: `15-pause-a.png` shows the pause menu after Enter; the second Enter produced `16-pause-b.png` with the menu closed; a third Enter produced `17-resume-c.png` with the menu visible again. This confirms menu toggling in the current QA battle page, but the sequence did not hold the first paused state for the interval, so it is not a countdown-freeze result.
