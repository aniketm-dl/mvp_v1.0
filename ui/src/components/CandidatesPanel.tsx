import { useStore } from "../store";
import { useState } from "react";

export default function CandidatesPanel() {
  const candidates = useStore(s => s.candidates);
  const setCandidates = useStore(s => s.setCandidates);

  const [newId, setNewId] = useState("");

  function add() {
    const id = newId.trim(); if (!id) return;
    setCandidates([...candidates, { id }]);
    setNewId("");
  }

  function remove(i: number) {
    const copy = [...candidates]; copy.splice(i,1);
    setCandidates(copy);
  }

  return (
    <div className="panel">
      <h3 style={{marginTop:0}}>Candidates</h3>
      <div className="col">
        {candidates.map((c, i)=>(
          <div key={i} className="row" style={{justifyContent:"space-between"}}>
            <div>{c.id}</div>
            <button className="btn" onClick={()=>remove(i)}>Remove</button>
          </div>
        ))}
        <div className="row">
          <input value={newId} onChange={(e)=>setNewId(e.target.value)} placeholder="Add ID e.g. A4"/>
          <button className="btn" onClick={add}>Add</button>
        </div>
      </div>
    </div>
  );
}
