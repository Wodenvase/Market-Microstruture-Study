use rand::prelude::*;
use rand::rngs::StdRng;
use rand::SeedableRng;
use rand_distr::Normal;
use std::fs::File;
use std::io::Write;

struct MarketState {
    price: f64,
    depth: f64,
    sigma: f64,
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let steps: usize = args
        .iter()
        .position(|s| s == "--steps")
        .and_then(|i| args.get(i + 1))
        .and_then(|s| s.parse().ok())
        .unwrap_or(10000);

    let alpha: f64 = args
        .iter()
        .position(|s| s == "--alpha")
        .and_then(|i| args.get(i + 1))
        .and_then(|s| s.parse().ok())
        .unwrap_or(0.5);
    let beta: f64 = args
        .iter()
        .position(|s| s == "--beta")
        .and_then(|i| args.get(i + 1))
        .and_then(|s| s.parse().ok())
        .unwrap_or(50.0);
    let gamma: f64 = args
        .iter()
        .position(|s| s == "--gamma")
        .and_then(|i| args.get(i + 1))
        .and_then(|s| s.parse().ok())
        .unwrap_or(1.0);

    let seed: u64 = args
        .iter()
        .position(|s| s == "--seed")
        .and_then(|i| args.get(i + 1))
        .and_then(|s| s.parse().ok())
        .unwrap_or(0);

    let output = args
        .iter()
        .position(|s| s == "--output")
        .and_then(|i| args.get(i + 1))
        .map(|s| s.as_str())
        .unwrap_or("data/sim.csv");

    let dt = 1.0 / 252.0; // 1 trading day normalized
    let mut rng: StdRng = if seed == 0 { StdRng::from_entropy() } else { StdRng::seed_from_u64(seed) };
    let noise_dist = Normal::new(0.0, 1.0).unwrap();

    let mut state = MarketState {
        price: 100.0,
        depth: 1.0,
        sigma: 0.001,
    };

    // simple leveraged fund state
    let mut fund_inventory: f64 = 0.0;
    let mut fund_equity: f64 = 1_000_000.0;
    let max_leverage: f64 = 10.0;

    // liquidity dynamics params (from CLI)

    // logging
    // ensure parent dirs exist for output path
    if let Some(parent) = std::path::Path::new(output).parent() {
        std::fs::create_dir_all(parent).ok();
    }
    let mut f = File::create(output).expect("create file");
    writeln!(
        f,
        "t,price,depth,sigma,noise_flow,fund_flow,forced_flow,inventory,equity"
    )
    .unwrap();

    // simple moving window for order variance approx
    let mut recent_flows: Vec<f64> = Vec::with_capacity(1000);

    for t in 0..steps {
        let time = t as f64 * dt;

        // noise trader order flow
        let noise_flow = noise_dist.sample(&mut rng) * 0.01 * (dt.sqrt());

        // fund strategy: trend follower on recent returns
        let momentum = if recent_flows.len() >= 5 {
            recent_flows.iter().rev().take(5).sum::<f64>() / 5.0
        } else {
            0.0
        };
        let fund_target = -1000.0 * momentum; // contrarian-ish for stability
        let fund_flow = (fund_target - fund_inventory) * 0.0001; // gradual

        // forced liquidation if leverage too high
        let position_value = fund_inventory * state.price;
        let leverage = if fund_equity.abs() < 1.0 { 0.0 } else { position_value.abs() / fund_equity };
        let mut forced_flow = 0.0;
        if leverage > max_leverage {
            // liquidate fraction
            forced_flow = -0.1 * fund_inventory; // sell 10% of inventory
        }

        // net order flow
        let dI = noise_flow + fund_flow + forced_flow;

        // price impact
        let dP = if state.depth.abs() < 1e-6 { dI.signum() * 1e-3 } else { dI / state.depth };
        state.price += dP;

        // update fund inventory and equity (market orders executed at mid-price)
        fund_inventory += fund_flow + forced_flow;
        fund_equity -= (fund_flow + forced_flow) * state.price; // naive P&L on trades

        // volatility proxy: use recent order flow variance / depth^2
        recent_flows.push(dI);
        if recent_flows.len() > 1000 { recent_flows.remove(0); }
        let var = if recent_flows.len() > 1 {
            let mean = recent_flows.iter().sum::<f64>() / recent_flows.len() as f64;
            recent_flows.iter().map(|x| (x - mean).powi(2)).sum::<f64>() / (recent_flows.len() as f64 - 1.0)
        } else { 1e-8 };
        state.sigma = (var.sqrt()) / (state.depth.max(1e-6));

        // liquidity dynamics Euler step: dL/dt = alpha - beta * sigma * L - gamma * InventoryRisk
        let inventory_risk = (fund_inventory.abs() / 10000.0).min(10.0);
        let dL = (alpha - beta * state.sigma * state.depth - gamma * inventory_risk) * dt;
        state.depth = (state.depth + dL).max(1e-4);

        writeln!(
            f,
            "{:.6},{:.6},{:.6},{:.6},{:.6},{:.6},{:.6},{:.6},{:.6}",
            time,
            state.price,
            state.depth,
            state.sigma,
            noise_flow,
            fund_flow,
            forced_flow,
            fund_inventory,
            fund_equity
        )
        .unwrap();
    }

    println!("Simulation complete — wrote {}", output);
}
