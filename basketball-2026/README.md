# Court Kings '26

A complete original 1v1 arcade basketball game inspired by the browser version of Basketball Stars. Built with plain HTML, CSS, JavaScript and Canvas. No account, installation, internet, ads, imported game code or third-party runtime dependencies are needed to play the standalone build.

## Play

Download **Court-Kings-2026.html** from `dist`, then open it in a current Chrome, Edge, Firefox or Safari browser. On a Chromebook, right-click the downloaded file and choose to open it in Chrome. If you downloaded the ZIP, extract it and open the HTML file at the top level.

For source development, run `npm start` in this folder and open `http://localhost:8080`. You do not need `npm install`.

## Included

- Solo matches against three AI difficulties.
- Local two-player matches on one keyboard.
- Eight-player knockout cup with quarterfinals, semifinals and a final.
- Unlimited shootaround with automatic loose-ball recovery.
- Twelve recognizable NBA star names and original animated cartoon portraits.
- Timed jump shots, three-pointers, dunks, rebounds, steals, physical blocks, pump fakes, double-tap dashes and heat-powered super shots.
- A 12-second possession clock, 60/90/120-second matches, buzzer-beater resolution and sudden-death overtime.
- Touch controls, optional synthesized sound, pause, fullscreen and a local solo win/loss record.
- Night Arena and Rooftop Court.

## Controls

| Action | Solo / practice | Local Player 1 | Local Player 2 |
| --- | --- | --- | --- |
| Move | A / D or left / right arrows | A / D | left / right arrows |
| Jump | W, up arrow or Space | W | up arrow |
| Shoot / steal | X, B or L | B | L |
| Pump fake / block | S or down arrow | S | down arrow |
| Dash | Shift or double-tap a direction | left Shift or double-tap A / D | right Shift or double-tap left / right |
| Super shot | Z, V or K | V | K |
| Pause | P or Escape | P or Escape | P or Escape |

Hold the shoot button, then release when the moving shot meter reaches the green band. Releasing near the opponent's rim while airborne triggers a dunk. With no possession, the shoot button attempts a steal. The block button jumps and raises your hands; the ball must physically enter your block reach. A failed steal briefly leaves you vulnerable. Build heat through baskets, steals and blocks. A full heat bar unlocks an unblockable, three-point super shot. Use the touch SHOOT button the same way: hold and release.

The horizontal distance from the attacked hoop determines the value: 3 points at 345 game units or farther, 2 points inside. A dunk is 2 points. Shots released before the buzzer may finish. A tie leads to overtime; the next basket wins. All-star difficulty is the default.

Local two-player mode is shared-screen play. It does not include online matchmaking. Touch controls operate Player 1; use a keyboard for both local players. Wins and losses are stored only in the current browser, when browser storage is available.

## 2026 roster

Stephen Curry, Luka Dončić, Shai Gilgeous-Alexander, Victor Wembanyama, Nikola Jokić, Giannis Antetokounmpo, LeBron James, Kevin Durant, Anthony Edwards, Jalen Brunson, Devin Booker and Donovan Mitchell.

Player selection is grounded in the NBA's published [2026 All-Star roster](https://www.nba.com/allstar/2026/roster) and [league player list](https://www.nba.com/players), consulted on October 8, 2026. The game uses individually named stars rather than claiming current team assignments. Jersey colors, ratings and abilities are custom arcade design, not official NBA statistics or licensed team uniforms. This is an independent fan project, not an official NBA or MadPuffers product.

## Code

| File | Responsibility |
| --- | --- |
| `src/engine.js` | Deterministic game logic, physics, AI, scoring and match rules. Also loads in Node for tests. |
| `src/render.js` | Canvas court, original player artwork, animations, shot meter and effects. |
| `src/app.js` | Menus, keyboard/touch input, tournament, audio and local records. |
| `styles.css` | Responsive application interface. |
| `scripts/serve.cjs` | Dependency-free local HTTP server. |
| `scripts/package.py` | Produces one offline HTML file and a ZIP with editable code. |
| `tests/engine.test.cjs` | Deterministic regression checks for gameplay and match rules. |

Run `npm test` for the physics/rules checks. Run `npm run build` with Python 3 installed to regenerate the standalone HTML and source ZIP. Playing the downloaded game does not require Node or Python.

## Scope

This is an original implementation of the arcade format. It does not promise identical Basketball Stars physics, animation or AI, and does not embed or scrape the original game. It is a browser application, not a Windows EXE or an app-store mobile package.
