import { useState } from "react";

const API = "http://127.0.0.1:8000";

function App() {
  const [destination, setDestination] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [budget, setBudget] = useState("");
  const [interests, setInterests] = useState("");

  const [loading, setLoading] = useState(false);
  const [simulating, setSimulating] = useState(false);
  const [agentData, setAgentData] = useState(null);
  const [disruptionData, setDisruptionData] = useState(null);
  const [error, setError] = useState("");

  const buildJourney = async () => {
    setLoading(true);
    setError("");
    setDisruptionData(null);

    try {
      const response = await fetch(`${API}/plan-trip`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          destination,
          start_date: startDate,
          end_date: endDate,
          budget: Number(budget) || 0,
          interests: interests
            .split(",")
            .map((item) => item.trim())
            .filter(Boolean),
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to build journey");
      }

      const data = await response.json();
      setAgentData(data);
    } catch (err) {
      setError("Could not connect to TravelPilot backend.");
    } finally {
      setLoading(false);
    }
  };

  const simulateDisruption = async () => {
    setSimulating(true);
    setError("");

    try {
      const response = await fetch(`${API}/simulate-disruption`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          destination,
          start_date: startDate,
          end_date: endDate,
          budget: Number(budget) || 0,
          interests: interests
            .split(",")
            .map((item) => item.trim())
            .filter(Boolean),
        }),
      });

      if (!response.ok) {
        throw new Error("Simulation failed");
      }

      const data = await response.json();
      setDisruptionData(data);
    } catch (err) {
      setError("Could not run disruption simulation.");
    } finally {
      setSimulating(false);
    }
  };

  const places = agentData?.real_places || [];
  const hotels = agentData?.hotels || [];
  const weather = agentData?.weather || {};
  const agent = agentData?.agent || {};

  const getTheme = () => {
    const city = destination.toLowerCase();

    if (city.includes("goa")) {
      return "goa";
    }

    if (city.includes("manali")) {
      return "manali";
    }

    if (city.includes("jaipur")) {
      return "jaipur";
    }

    if (city.includes("bengaluru") || city.includes("bangalore")) {
      return "bengaluru";
    }

    return "default";
  };

  return (
    <div className={`app ${getTheme()}`}>
      <style>{`
        * {
          box-sizing: border-box;
        }

        body {
          margin: 0;
          font-family: Inter, Arial, sans-serif;
          background: #081416;
        }

        .app {
          min-height: 100vh;
          color: white;
          background:
            linear-gradient(
              rgba(5, 20, 24, 0.58),
              rgba(5, 15, 20, 0.88)
            ),
            url("https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=2200&q=90")
            center / cover fixed;
          padding-bottom: 60px;
        }

        .app.goa {
          background:
            linear-gradient(
              rgba(0, 55, 65, 0.48),
              rgba(3, 24, 30, 0.88)
            ),
            url("https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=2200&q=90")
            center / cover fixed;
        }

        .app.manali {
          background:
            linear-gradient(
              rgba(25, 45, 60, 0.48),
              rgba(8, 18, 28, 0.9)
            ),
            url("https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=2200&q=90")
            center / cover fixed;
        }

        .app.jaipur {
          background:
            linear-gradient(
              rgba(80, 45, 25, 0.48),
              rgba(35, 20, 15, 0.9)
            ),
            url("https://images.unsplash.com/photo-1477587458883-47145ed94245?auto=format&fit=crop&w=2200&q=90")
            center / cover fixed;
        }

        .app.bengaluru {
          background:
            linear-gradient(
              rgba(15, 65, 45, 0.45),
              rgba(5, 25, 20, 0.9)
            ),
            url("https://images.unsplash.com/photo-1596176530529-78163a4f7af2?auto=format&fit=crop&w=2200&q=90")
            center / cover fixed;
        }

        .navbar {
          height: 76px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0 7%;
          border-bottom: 1px solid rgba(255,255,255,0.12);
          background: rgba(4, 15, 18, 0.55);
          backdrop-filter: blur(18px);
        }

        .logo {
          font-size: 25px;
          font-weight: 800;
          letter-spacing: -0.5px;
        }

        .logo span {
          color: #66e3c4;
        }

        .nav-text {
          color: #c7d8d8;
          font-size: 14px;
        }

        .hero {
          max-width: 1150px;
          margin: 0 auto;
          padding: 70px 25px 35px;
          text-align: center;
        }

        .hero h1 {
          margin: 0;
          font-size: clamp(42px, 7vw, 76px);
          line-height: 1;
          letter-spacing: -3px;
        }

        .hero h1 span {
          color: #69e6c5;
        }

        .hero p {
          max-width: 700px;
          margin: 22px auto;
          color: #c7d7d8;
          font-size: 18px;
          line-height: 1.6;
        }

        .planner {
          max-width: 1100px;
          margin: 20px auto 45px;
          padding: 28px;
          border: 1px solid rgba(255,255,255,0.14);
          border-radius: 24px;
          background: rgba(8, 24, 28, 0.68);
          backdrop-filter: blur(20px);
          box-shadow: 0 20px 70px rgba(0,0,0,0.25);
        }

        .form-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 16px;
        }

        .field {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .field.full {
          grid-column: 1 / -1;
        }

        .field label {
          color: #a9c0c1;
          font-size: 13px;
          font-weight: 600;
        }

        input {
          width: 100%;
          padding: 15px 16px;
          border: 1px solid rgba(255,255,255,0.14);
          border-radius: 13px;
          outline: none;
          color: white;
          background: rgba(255,255,255,0.07);
          font-size: 15px;
        }

        input:focus {
          border-color: #69e6c5;
        }

        .actions {
          display: flex;
          gap: 12px;
          margin-top: 22px;
          flex-wrap: wrap;
        }

        button {
          border: none;
          border-radius: 13px;
          padding: 14px 22px;
          font-size: 15px;
          font-weight: 700;
          cursor: pointer;
          transition: 0.2s ease;
        }

        .primary {
          color: #06201d;
          background: #69e6c5;
        }

        .secondary {
          color: white;
          background: rgba(255,255,255,0.1);
          border: 1px solid rgba(255,255,255,0.15);
        }

        button:hover {
          transform: translateY(-2px);
        }

        button:disabled {
          opacity: 0.6;
          cursor: not-allowed;
          transform: none;
        }

        .container {
          max-width: 1150px;
          margin: auto;
          padding: 0 25px;
        }

        .section-title {
          margin: 45px 0 18px;
          font-size: 25px;
        }

        .section-subtitle {
          color: #9eb4b5;
          margin-top: -8px;
          margin-bottom: 20px;
        }

        .grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 18px;
        }

        .card {
          border: 1px solid rgba(255,255,255,0.13);
          border-radius: 20px;
          padding: 21px;
          background: rgba(9, 28, 32, 0.72);
          backdrop-filter: blur(18px);
          box-shadow: 0 14px 45px rgba(0,0,0,0.18);
        }

        .card h3 {
          margin: 0 0 9px;
          font-size: 18px;
        }

        .card p {
          color: #b8c9ca;
          line-height: 1.55;
          font-size: 14px;
        }

        .tag {
          display: inline-block;
          padding: 6px 10px;
          border-radius: 20px;
          color: #75e8ca;
          background: rgba(105,230,197,0.1);
          font-size: 12px;
          margin-bottom: 12px;
        }

        .agent-grid {
          display: grid;
          grid-template-columns: repeat(5, 1fr);
          gap: 12px;
        }

        .agent-card {
          min-height: 160px;
          padding: 18px;
          border-radius: 18px;
          background: rgba(7, 25, 29, 0.72);
          border: 1px solid rgba(255,255,255,0.12);
        }

        .agent-card .number {
          font-size: 12px;
          color: #69e6c5;
          font-weight: 800;
        }

        .agent-card h3
        `}</style>

      <nav className="navbar">
        <div className="logo">
          Travel<span>Pilot</span>
        </div>

        <div className="nav-text">
          Intelligent Trip Planning Agent
        </div>
      </nav>

      <section className="hero">
        <h1>
          Travel with a <span>plan.</span>
          <br />
          Move with the <span>moment.</span>
        </h1>

        <p>
          Your journey, always in motion. TravelPilot continuously adapts
          your trip when plans change.
        </p>
      </section>

      <section className="planner">
        <div className="form-grid">
          <div className="field full">
            <label>Destination</label>
            <input
              value={destination}
              onChange={(e) => setDestination(e.target.value)}
              placeholder="Goa, Manali, Jaipur..."
            />
          </div>

          <div className="field">
            <label>Start date</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
            />
          </div>

          <div className="field">
            <label>End date</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
            />
          </div>

          <div className="field">
            <label>Budget</label>
            <input
              type="number"
              value={budget}
              onChange={(e) => setBudget(e.target.value)}
              placeholder="₹ 20,000"
            />
          </div>

          <div className="field">
            <label>Interests</label>
            <input
              value={interests}
              onChange={(e) => setInterests(e.target.value)}
              placeholder="beaches, food, culture..."
            />
          </div>
        </div>

        <div className="actions">
          <button
            className="primary"
            onClick={buildJourney}
            disabled={loading}
          >
            {loading ? "Planning..." : "Build My Journey →"}
          </button>

          <button
            className="secondary"
            onClick={simulateDisruption}
            disabled={simulating}
          >
            {simulating
              ? "Simulating..."
              : "⚠ Simulate Disruption"}
          </button>
        </div>

        {error && <div className="error">{error}</div>}
      </section>

      {agentData && (
        <main className="container">

          <h2 className="section-title">
            🧠 TravelPilot Agent
          </h2>

          <div className="agent-grid">

            <div className="agent-card">
              <div className="number">01</div>
              <h3>Observe</h3>
              <p>
                {agent.observe ||
                  "TravelPilot observes destination, weather, places and hotels."}
              </p>
            </div>

            <div className="agent-card">
              <div className="number">02</div>
              <h3>Reason</h3>
              <p>
                {agent.reason ||
                  agentData.reasoning ||
                  "AI evaluates the trip requirements and available information."}
              </p>
            </div>

            <div className="agent-card">
              <div className="number">03</div>
              <h3>Act</h3>
              <p>
                {agent.act ||
                  "TravelPilot creates a suitable dynamic journey plan."}
              </p>
            </div>

            <div className="agent-card">
              <div className="number">04</div>
              <h3>Verify</h3>
              <p>
                {agent.verify ||
                  "TravelPilot verifies the collected travel information."}
              </p>
            </div>

            <div className="agent-card">
              <div className="number">05</div>
              <h3>Adapt</h3>
              <p>
                {agent.adapt ||
                  "TravelPilot remains ready to adapt the journey."}
              </p>
            </div>

          </div>

          <h2 className="section-title">
            📍 Real Places
          </h2>

          <div className="grid">
            {places.length > 0 ? (
              places.map((place, index) => (
                <div className="card" key={index}>
                  <span className="tag">
                    {place.category || "Place"}
                  </span>

                  <h3>
                    {place.name?.split(",")[0] || "Place"}
                  </h3>

                  <p>
                    📍 {place.name || "Location information unavailable"}
                  </p>
                </div>
              ))
            ) : (
              <div className="card empty">
                No real places found.
              </div>
            )}
          </div>

          <h2 className="section-title">
            🏨 Real Hotels
          </h2>

          <div className="grid">
            {hotels.length > 0 ? (
              hotels.map((hotel, index) => (
                <div className="card" key={index}>
                  <span className="tag">Hotel</span>

                  <h3>
                    {hotel.name?.split(",")[0] || "Hotel"}
                  </h3>

                  <p>
                    📍 {hotel.name || "Location information unavailable"}
                  </p>

                  {hotel.stars && (
                    <p>⭐ {hotel.stars} star property</p>
                  )}

                  {hotel.website && (
                    <p>
                      🌐 {hotel.website}
                    </p>
                  )}
                </div>
              ))
            ) : (
              <div className="card empty">
                No real hotels found.
              </div>
            )}
          </div>

          <h2 className="section-title">
            🌦️ Destination Weather
          </h2>

          <div className="card weather">
            <div className="weather-temp">
              {weather.temperature !== undefined
                ? `${weather.temperature}°`
                : "--"}
            </div>

            <div>
              <h3>
                {weather.description || "Weather information"}
              </h3>

              <p>
                {weather.wind_speed !== undefined
                  ? `Wind: ${weather.wind_speed} km/h`
                  : "Current weather conditions considered by the agent."}
              </p>
            </div>
          </div>

          <h2 className="section-title">
            🗺️ Your Dynamic Journey
          </h2>

          <div className="card">
            {agentData.plan?.length > 0 ? (
              agentData.plan.map((day, index) => (
                <div className="plan-day" key={index}>
                  <h3>
                    Day {day.day || index + 1}
                  </h3>

                  <ul>
                    {(day.activities || []).map(
                      (activity, activityIndex) => (
                        <li key={activityIndex}>
                          {activity}
                        </li>
                      )
                    )}
                  </ul>
                </div>
              ))
            ) : (
              <p className="empty">
                No itinerary generated yet.
              </p>
            )}
          </div>

          {agentData.summary && (
            <>
              <h2 className="section-title">
                ✨ Agent Summary
              </h2>

              <div className="card success">
                <p>{agentData.summary}</p>
              </div>
            </>
          )}

          {agentData.warnings?.length > 0 && (
            <>
              <h2 className="section-title">
                ⚠️ Travel Warnings
              </h2>

              <div className="card disruption">
                {agentData.warnings.map((warning, index) => (
                  <p key={index}>• {warning}</p>
                ))}
              </div>
            </>
          )}

          {disruptionData && (
            <>
              <h2 className="section-title">
                🚨 Disruption Simulation
              </h2>

              <div
                className={`card ${
                  disruptionData.status === "disruption_detected"
                    ? "disruption"
                    : "success"
                }`}
              >
                <span className="tag">
                  {disruptionData.status === "disruption_detected"
                    ? "Disruption detected"
                    : "No major disruption"}
                </span>

                <h3>
                  {disruptionData.description ||
                    "Simulation completed."}
                </h3>

                {disruptionData.adaptation && (
                  <p>
                    <strong>🤖 AI Adaptation:</strong>{" "}
                    {disruptionData.adaptation}
                  </p>
                )}

                {disruptionData.agent?.observe && (
                  <p>
                    <strong>Observe:</strong>{" "}
                    {disruptionData.agent.observe}
                  </p>
                )}

                {disruptionData.agent?.reason && (
                  <p>
                    <strong>Reason:</strong>{" "}
                    {disruptionData.agent.reason}
                  </p>
                )}

                {disruptionData.agent?.act && (
                  <p>
                    <strong>Act:</strong>{" "}
                    {disruptionData.agent.act}
                  </p>
                )}

                {disruptionData.agent?.verify && (
                  <p>
                    <strong>Verify:</strong>{" "}
                    {disruptionData.agent.verify}
                  </p>
                )}

                {disruptionData.agent?.adapt && (
                  <p>
                    <strong>Adapt:</strong>{" "}
                    {disruptionData.agent.adapt}
                  </p>
                )}
              </div>
            </>
          )}

        </main>
      )}
    </div>
  );
}

export default App;