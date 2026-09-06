import assert from "node:assert/strict";
import test from "node:test";
import {loadAuthority} from "../src/load.js";
import {createHarnessProjection} from "../src/harness-authority.js";
import {deriveCalculatorProjection} from "../src/mechanics-selectors.js";
import {validateSemantics} from "../src/validate.js";

test("Pyrokinesis Apex reaches both consumers with its separate fire packet",async()=>{
  const {authority}=await loadAuthority();
  const calculator=deriveCalculatorProjection(authority),harness=await createHarnessProjection();
  assert.deepEqual(calculator.harness_mechanics.psionic_apex,harness.core.psionic_apex);
  assert.deepEqual(harness.core.psionic_apex.pyrokinesis_manifested_strike_hit,{discipline_id:"pyrokinesis",uses_per_attack_action:1,reset:"start_of_each_attack_action",damage_type:"fire",damage:{kind:"dice",count:2,sides:8},critical_dice_multiplier:1,psi_cost:0,blood_tax:0});
  assert.equal(harness.core.psionic_apex.minimum_level,18);
  assert.equal(harness.core.psionic_apex.psychokinesis_manifested_strike_hit.damage.count,3);
  const prose=JSON.stringify(authority.entities.find(entity=>entity.id==="advanced_training_progression")!.content);
  for(const phrase of ["Pyrokinesis Maturation", "2d8 fire damage to that creature", "This packet has no Overload tier", "even when the strike delivers a Tier-2 rider or uses the Holdout Option"]){assert.ok(prose.includes(phrase),phrase);}
});

test("Apex cannot drift to per-strike, resource-paid, critical-doubled, or force damage",async()=>{
  const {authority}=await loadAuthority();
  for(const [key,value] of [["uses_per_attack_action",2],["critical_dice_multiplier",2],["damage_type","force"],["psi_cost",1],["blood_tax",1]] as const){
    const candidate:any=structuredClone(authority);
    candidate.entities.find((entity:any)=>entity.id==="advanced_training_progression").system_mechanics.psionic_apex.pyrokinesis_manifested_strike_hit[key]=value;
    assert.ok(validateSemantics(candidate).some(diagnostic=>diagnostic.code==="harness.psionic_apex"),key);
  }
});
