// fetch/src/x402-mock/server.ts
// Plan 01-07 Task 1 — self-hosted node:http 402 mock server.
//
// Behavioral contract (RESEARCH.md §F + checker I10 / live-probe drift adaptation):
//   - GET /mock/weather without X-PAYMENT → 402 + x402 v1 PaymentRequirements
//     JSON body with accepts[0].network='base-sepolia' and asset=Base Sepolia USDC.
//   - GET /mock/weather with valid base64-encoded X-PAYMENT (scheme='exact',
//     network='base-sepolia', payload.signature=0x{130 hex}, payload.authorization.from=
//     0x{40 hex}) → 200 + X-PAYMENT-RESPONSE base64 JSON
//     {success:true, transaction, network, payer, errorReason:null}.
//   - Malformed X-PAYMENT → 402 with X-PAYMENT-RESPONSE carrying success=false
//     and errorReason.
//
// STACK DRIFT (documented in 01-07-SUMMARY.md): the plan body's static text
// proposed `accepts[0].network='eip155:84532'` (CAIP-2 form). Live probe of
// @x402/evm v2.13 + @x402/fetch v2.13 with `new x402Client()` +
// `registerExactEvmScheme(client, { signer })` revealed:
//   - x402Version: 1 → ExactEvmSchemeV1 registers on NAMED networks
//     (`ethereum`, `base-sepolia`, `base`, ...). It does NOT recognise
//     `eip155:84532` and throws "No network/scheme registered for x402 version: 1".
//   - x402Version: 2 → ExactEvmScheme registers on `eip155:*`. The v2 schema
//     uses `amount` (not `maxAmountRequired`), top-level `resource: {url, method}`,
//     and emits a payload envelope with `accepted` (no top-level `scheme`/`network`).
//     The header is `PAYMENT-SIGNATURE`, NOT `X-PAYMENT`.
// The plan's structural validator (scheme/network/payload.signature/
// payload.authorization.from on the X-PAYMENT header) matches the v1 envelope.
// We therefore land v1 PaymentRequirements with network='base-sepolia'. The
// functional contract (402 → sign → retry → 200) per RESEARCH §F is invariant.
//
// Phase 1 ships HEADER-ONLY mode by default. X402_MOCK_REAL_SETTLE=1 is the
// opt-in escalation for manual developer-machine validation against a real
// Base Sepolia faucet-funded wallet (not exercised in CI).
//
// timestamp in success body uses ISO-8601 string per checker M13 — matches the
// cost-ledger Datetime[us] polars schema. Fixed (not Date.now()) for
// deterministic re-run output.

import {
  createServer,
  type IncomingMessage,
  type ServerResponse,
  type Server,
} from 'node:http';
import { randomBytes } from 'node:crypto';

const X402_VERSION = 1;
const BASE_SEPOLIA_USDC = '0x036cbd53842c5426634e7929541ec2318f3dcf7e';

// x402 v2.13 ExactEvmScheme requires `extra.name` + `extra.version` for the
// EIP-712 domain construction (TransferWithAuthorization on USDC). Without
// these, createPaymentPayload throws BEFORE producing a signature.
// USDC on Base Sepolia uses EIP-712 domain {name: 'USDC', version: '2'} —
// matches mainnet Circle deployment.
export const PAYMENT_REQUIREMENTS = {
  x402Version: X402_VERSION,
  accepts: [
    {
      scheme: 'exact',
      network: 'base-sepolia',
      maxAmountRequired: '1000', // 0.001 USDC (6 decimals)
      resource: '/mock/weather',
      description: 'Mock 402 endpoint for x402 round-trip test',
      payTo: '0x000000000000000000000000000000000000dEaD',
      asset: BASE_SEPOLIA_USDC,
      mimeType: 'application/json',
      maxTimeoutSeconds: 60,
      extra: { name: 'USDC', version: '2' },
    },
  ],
};

function makeStubTxHash(): string {
  return '0x' + randomBytes(32).toString('hex');
}

export function validateXPaymentHeader(b64: string): {
  ok: boolean;
  payer?: string;
  reason?: string;
} {
  try {
    const decoded = JSON.parse(Buffer.from(b64, 'base64').toString());
    if (decoded.scheme !== 'exact') {
      return { ok: false, reason: 'scheme must be "exact"' };
    }
    if (decoded.network !== 'base-sepolia') {
      return { ok: false, reason: 'network mismatch' };
    }
    const sig = decoded.payload?.signature;
    if (typeof sig !== 'string' || !/^0x[0-9a-fA-F]{130}$/.test(sig)) {
      return { ok: false, reason: 'invalid signature shape' };
    }
    const payer = decoded.payload?.authorization?.from;
    if (typeof payer !== 'string' || !/^0x[0-9a-fA-F]{40}$/.test(payer)) {
      return { ok: false, reason: 'invalid payer' };
    }
    return { ok: true, payer };
  } catch (e) {
    return { ok: false, reason: `header parse failed: ${(e as Error).message}` };
  }
}

function paymentResponseHeader(
  success: boolean,
  tx: string | null,
  payer: string | null,
  err: string | null,
): string {
  return Buffer.from(
    JSON.stringify({
      success,
      transaction: tx,
      network: 'base-sepolia',
      payer,
      errorReason: err,
    }),
  ).toString('base64');
}

export function startMockServer(
  port = 0,
): Promise<{ server: Server; port: number }> {
  const server = createServer((req: IncomingMessage, res: ServerResponse) => {
    if (req.url !== '/mock/weather') {
      res.writeHead(404);
      res.end();
      return;
    }
    const xPay = req.headers['x-payment'] as string | undefined;
    if (!xPay) {
      res.writeHead(402, { 'content-type': 'application/json' });
      res.end(JSON.stringify(PAYMENT_REQUIREMENTS));
      return;
    }
    const v = validateXPaymentHeader(xPay);
    if (!v.ok) {
      res.writeHead(402, {
        'content-type': 'application/json',
        'x-payment-response': paymentResponseHeader(
          false,
          null,
          null,
          v.reason ?? 'invalid',
        ),
      });
      res.end(JSON.stringify({ ...PAYMENT_REQUIREMENTS, error: v.reason }));
      return;
    }
    const tx = makeStubTxHash();
    res.writeHead(200, {
      'content-type': 'application/json',
      'x-payment-response': paymentResponseHeader(true, tx, v.payer!, null),
    });
    // NOTE: per checker M13, timestamp uses ISO-8601 string (matches cost-ledger
    // Datetime[us] polars schema from Plan 01-02). Fixed value (not Date.now())
    // for deterministic output across reruns.
    res.end(
      JSON.stringify({
        weather: 'mock-sunny',
        timestamp: '1970-01-01T00:00:00.000Z',
      }),
    );
  });
  return new Promise((resolve) => {
    server.listen(port, () => {
      resolve({ server, port: (server.address() as { port: number }).port });
    });
  });
}
