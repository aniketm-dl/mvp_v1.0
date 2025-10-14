import PersonaList from "./components/PersonaList";
import ChatPanel from "./components/ChatPanel";
import CandidatesPanel from "./components/CandidatesPanel";
import ScenarioPanel from "./components/ScenarioPanel";
import ResultsPanel from "./components/ResultsPanel";

export default function App() {
  return (
    <div className="app">
      <header>
        <h2 style={{margin:0}}>Darpan What-If Playground</h2>
        <span className="small">Deterministic twins. Grounded reasons.</span>
      </header>
      <PersonaList />
      <main>
        <ChatPanel />
        <CandidatesPanel />
      </main>
      <ScenarioPanel />
      <ResultsPanel />
    </div>
  );
}
