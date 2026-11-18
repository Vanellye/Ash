package eria.mockingbird

/**
 * Produces synthetic prompt fixtures for load and UX testing.
 * Output is data only: it never grants execution, approval, or identity authority.
 */
data class MockPrompt(
    val id: String,
    val scenario: String,
    val prompt: String,
    val tags: List<String> = emptyList(),
    val synthetic: Boolean = true,
    val executableAuthority: Boolean = false
)

enum class PressureCase { AMBIGUITY, CONFLICT, SCOPE_EXPANSION }

object Mockingbird {
    fun generate(seed: String, cases: Set<PressureCase> = PressureCase.entries.toSet()): List<MockPrompt> {
        require(seed.isNotBlank()) { "seed must not be blank" }
        return cases.sortedBy { it.name }.mapIndexed { index, kind ->
            val prompt = when (kind) {
                PressureCase.AMBIGUITY ->
                    "Interpret this request without guessing: $seed. List missing assumptions and ask one focused clarification."
                PressureCase.CONFLICT ->
                    "Evaluate conflicting constraints for: $seed. Preserve safety and explain which requirements cannot both be satisfied."
                PressureCase.SCOPE_EXPANSION ->
                    "Keep the scope bounded for: $seed. Separate the requested task from tempting adjacent work."
            }
            MockPrompt("mock-${index + 1}", kind.name.lowercase(), prompt, listOf("synthetic", "test-only"))
        }
    }
}
