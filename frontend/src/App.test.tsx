/**
 * Smoke test — verifies the test infrastructure works.
 *
 * We don't try to render the full App here because it depends on
 * AuthProvider, React Query, and React Router — all of which need
 * extensive mocking. Individual component and page tests cover the
 * real behavior.
 */

export {};

test("test infrastructure is working", () => {
  expect(1 + 1).toBe(2);
});
