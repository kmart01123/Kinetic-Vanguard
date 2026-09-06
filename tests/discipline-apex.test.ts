import assert from "node:assert/strict";
import test from "node:test";
import {loadAuthority} from "../src/load.js";
import {createHarnessProjection} from "../src/harness-authority.js";
import {deriveCalculatorProjection} from "../src/mechanics-selectors.js";
import {validateSemantics} from "../src/validate.js";

test("Discipline Apex reaches both consumers with separate native damage packets",async()=>{
  const {authority}=await loadAuthority();
  const calculator=deriveCalculatorProjection(authority),harness=await createHarnessProjection();
  assert.deepEqual(calculator.harness_mechanics.psionic_apex,harness.core.psionic_apex);
  for(const [discipline,type] of [["cryokinesis","cold"],["pyrokinesis","fire"],["psychokinesis","force"],["electrokinesis","lightning"]] as const){
    assert.deepEqual(harness.core.psionic_apex[`${discipline}_manifested_strike_hit`],{discipline_id:discipline,uses_per_attack_action:1,reset:"start_of_each_attack_action",damage_type:type,damage:{kind:"dice",count:3,sides:8},critical_dice_multiplier:1,psi_cost:0,blood_tax:0});
  }
  assert.equal(harness.core.psionic_apex.minimum_level,18);
  const prose=JSON.stringify(authority.entities.find(entity=>entity.id==="advanced_training_progression")!.content);
  for(const phrase of ["Discipline Maturation", "3d8 damage to that creature", "cold for Cryokinesis, fire for Pyrokinesis, force for Psychokinesis, and lightning for Electrokinesis", "This packet has no Overload tier", "even when the strike delivers a Tier-2 rider or uses the Holdout Option"]){assert.ok(prose.includes(phrase),phrase);}
});

test("Apex cannot drift to per-strike, resource-paid, critical-doubled, or incorrect damage types",async()=>{
  const {authority}=await loadAuthority();
  for(const discipline of ["cryokinesis","pyrokinesis","psychokinesis","electrokinesis"]){
  for(const [key,value] of [["uses_per_attack_action",2],["critical_dice_multiplier",2],["damage_type","acid"],["psi_cost",1],["blood_tax",1]] as const){
    const candidate:any=structuredClone(authority);
    candidate.entities.find((entity:any)=>entity.id==="advanced_training_progression").system_mechanics.psionic_apex[`${discipline}_manifested_strike_hit`][key]=value;
    assert.ok(validateSemantics(candidate).some(diagnostic=>diagnostic.code==="harness.psionic_apex"),key);
  }
  }
});
