<WebscoutCopilotInstructions>
  <Purpose>
    Concise, actionable guidance so an AI coding agent can be productive immediately when editing Webscout.
  </Purpose>
  
  <AgentOrchestration>
    <Overview>
      If the subagent tool is available, the main Copilot agent acts strictly as an orchestrator.
      All research, planning, and heavy reasoning MUST be delegated to specialized subagents.
      Note: There may be other subagents available beyond those listed below.
      Always call multiple subagents in parallel.
      Firstly break down task into subtasks.
      Then, for each subtask, call the appropriate subagent or custom agent.
    </Overview>

    <AvailableSubagents>
      <Subagent>
        <Name>Reverse</Name>
        <Role>Reverse Engineering & Provider Discovery Agent</Role>
        <Responsibilities>
          <Item>Inspect websites or APIs</Item>
          <Item>Extract endpoints, headers, payloads, auth, streaming patterns</Item>
          <Item>Generate production-ready Provider classes</Item>
        </Responsibilities>
        <WhenToCall>
          <Condition>User asks to reverse engineer a website or API</Condition>
          <Condition>User requests a new Provider implementation</Condition>
          <Condition>Unknown or undocumented API behavior</Condition>
        </WhenToCall>
        <MustNot>
          <Item>Modify unrelated files</Item>
          <Item>Plan multi-file refactors</Item>
        </MustNot>
      </Subagent>
      <Subagent>
        <Name>Plan</Name>
        <Role>Planning & Task Decomposition Agent</Role>
        <Responsibilities>
          <Item>Break large requests into discrete tasks</Item>
          <Item>Define execution order</Item>
          <Item>Identify required files and agents</Item>
        </Responsibilities>
        <WhenToCall>
          <Condition>Task spans multiple files</Condition>
          <Condition>Complex refactors or new subsystems</Condition>
          <Condition>Ambiguous or high-level user requests</Condition>
        </WhenToCall>
        <MustNot>
          <Item>Write production code</Item>
          <Item>Perform API research</Item>
        </MustNot>
      </Subagent>
    </AvailableSubagents>

    <AgentCallingRules>
      <Rule>
        If the subagent tool is available, the main agent MUST decide which subagent to call
        before acting.
      </Rule>
      <Rule>
        If the subagent tool is available, ONE or More subagents may be active per task chunk.
      </Rule>
      <Rule>
        If the subagent tool is available and a task involves multiple concerns, call Plan first.
      </Rule>
      <Rule>
        If the subagent tool is available, never mix reverse engineering, planning, and
        documentation in one agent.
      </Rule>
    </AgentCallingRules>

    <ExecutionFlow>
      <Flow>
        <Step>Receive user request</Step>
        <Step>Classify intent (Reverse / Docstring / Plan)</Step>
        <Step>If subagent tool is available, delegate to appropriate subagent</Step>
        <Step>If subagent tool is available, receive result</Step>
        <Step>Apply or present result</Step>
      </Flow>
    </ExecutionFlow>
  </AgentOrchestration>

  <CriticalContextWindowManagement>
    <Rule>ALWAYS work in discrete, focused steps</Rule>
    <Rule>Use runSubagent for tasks when the subagent tool is available</Rule>
    <Rule>Break large tasks into smaller chunks</Rule>
    <Rule>Avoid reading large files entirely; search for specific code first using codebase-retrieval</Rule>
    <Rule>Never batch too many operations; use subagents or groups of 3–5 files</Rule>
    <Guidance>
      Always, delegate to a subagent rather than risk output truncation.
    </Guidance>
  </CriticalContextWindowManagement>

  <CodeQualityTools>
    <Approved>
      <Tool>
        <Name>Ruff</Name>
        <Command>uvx ruff check .</Command>
        <Purpose>Linting &amp; formatting</Purpose>
        <Status>USE</Status>
      </Tool>
      <Tool>
        <Name>Ty</Name>
        <Command>uvx ty check .</Command>
        <Purpose>Type checking</Purpose>
        <Status>USE</Status>
      </Tool>
    </Approved>
    <Disallowed>
      <Tool>mypy</Tool>
      <Tool>pyright</Tool>
      <Tool>pylint</Tool>
      <Tool>flake8</Tool>
      <Tool>black</Tool>
    </Disallowed>
    <Rationale>
      Ruff is extremely fast and handles linting/formatting. Ty is a modern, faster alternative
      to mypy/pyright. Multiple tools cause conflicts and slow development.
    </Rationale>
  </CodeQualityTools>

  <ProjectStructure>
    <Root>webscout/</Root>
    <Subsystems>
      <Subsystem>
        <Path>webscout/Provider/</Path>
        <Description>AI provider implementations</Description>
        <Variants>
          <Variant>
            <Path>OPENAI/</Path>
            <Description>OpenAI-compatible wrappers</Description>
          </Variant>
          <Variant>
            <Path>TTI/</Path>
            <Description>Text-to-Image providers</Description>
          </Variant>
        </Variants>
      </Subsystem>
      <Subsystem>
        <Path>webscout/search/</Path>
        <Description>Search engine backends</Description>
      </Subsystem>
      <Subsystem>
        <Path>webscout/server/</Path>
        <Description>FastAPI OpenAI-compatible API server</Description>
      </Subsystem>
      <Subsystem>
        <Path>webscout/cli.py</Path>
        <Description>CLI entrypoint</Description>
      </Subsystem>
      <Subsystem>
        <Path>webscout/swiftcli/</Path>
        <Description>CLI helpers</Description>
      </Subsystem>
      <Subsystem>
        <Path>webscout/Extra/</Path>
        <Description>Misc utilities</Description>
      </Subsystem>
      <Subsystem>
        <Path>docs/</Path>
        <Description>Human-facing documentation</Description>
      </Subsystem>
    </Subsystems>
  </ProjectStructure>

  <DeveloperWorkflows>
    <Environment>
      <Rule>Always use uv; never bare python or pip</Rule>
    </Environment>
    <Commands>
      <Command>uv pip install &lt;package&gt;</Command>
      <Command>uv pip uninstall &lt;package&gt;</Command>
      <Command>uv run &lt;command&gt;</Command>
      <Command>uv run --extra api webscout-server</Command>
      <Command>uv sync --extra dev --extra api</Command>
      <Command>uv run webscout</Command>
      <Command>uv run --extra api webscout-server -- --debug</Command>
      <Command>uv run pytest</Command>
      <Command>uv run ruff .</Command>
    </Commands>
  </DeveloperWorkflows>

  <ProviderConventions>
    <OpenAICompatibleProviders>
      <Discovery>
        <Rule>Must live under webscout/Provider/OPENAI/</Rule>
        <Rule>Must be imported in webscout/Provider/OPENAI/__init__.py</Rule>
        <Rule>Must subclass OpenAICompatibleProvider</Rule>
        <Rule>Must define required_auth attribute</Rule>
        <Rule>required_auth must be False to be publicly registered</Rule>
      </Discovery>
      <Optional>
        <Feature>AVAILABLE_MODELS</Feature>
      </Optional>
      <Example><![CDATA[
class MyProvider(OpenAICompatibleProvider):
    required_auth = False
    AVAILABLE_MODELS = ["fast", "accurate"]

    @property
    def models(self):
        return type("M", (), {"list": lambda self: ["fast", "accurate"]})()

    def chat(self):
        ...
      ]]></Example>
    </OpenAICompatibleProviders>

    <NormalProviders>
      <Rules>
        <Rule>Subclass webscout.AIbase.Provider</Rule>
        <Rule>Implement ask(), chat(), get_message()</Rule>
        <Rule>Export via webscout/Provider/__init__.py</Rule>
        <Rule>Use requests.Session</Rule>
        <Rule>Add unit tests under tests/providers/</Rule>
        <Rule>Update Provider.md and docs/</Rule>
      </Rules>
    </NormalProviders>

    <TTIProviders>
      <Rule>Follow patterns in webscout/Provider/TTI/</Rule>
      <Rule>Discovered via initialize_tti_provider_map</Rule>
    </TTIProviders>
  </ProviderConventions>

  <CLIConventions>
    <Framework>swiftcli</Framework>
    <Rules>
      <Rule>Use @app.command()</Rule>
      <Rule>Use @option()</Rule>
      <Rule>Async handlers supported</Rule>
      <Rule>Use rich for console output</Rule>
    </Rules>
  </CLIConventions>

  <LoggingAndErrors>
    <Internal>litprinter.ic</Internal>
    <UserFacing>Rich console</UserFacing>
    <Server>
      <Rule>Use FastAPI exceptions</Rule>
      <Rule>Follow OpenAI-compatible error shapes</Rule>
    </Server>
  </LoggingAndErrors>

  <ReleaseAndCI>
    <Versioning>Date-based in webscout/version.py</Versioning>
    <Automation>
      <Workflow>.github/workflows/publish-to-pypi.yml</Workflow>
      <Workflow>release-with-changelog.yml</Workflow>
    </Automation>
  </ReleaseAndCI>

  <TestingGuidelines>
    <Rule>Add tests for new behavior</Rule>
    <Rule>Validate provider discovery and model registration</Rule>
    <Rule>Use pytest under tests/</Rule>
    <Structure>
      <Rule>Place unit tests in tests/providers/ for provider implementations</Rule>
      <Rule>Use unittest.TestCase for unit tests with setUp() methods</Rule>
      <Rule>Mock external dependencies using FakeResp or similar patterns</Rule>
      <Rule>Test parsing, validation, and error handling</Rule>
      <Rule>Name test files as test_&lt;provider_name&gt;.py</Rule>
      <Rule>Interactive/stress tests use pytestmark = pytest.mark.skip() to avoid running in CI</Rule>
      <Rule>All test files must pass: uvx ruff check . and uvx ty check .</Rule>
    </Structure>
  </TestingGuidelines>

  <DocsToUpdate>
    <File>docs/</File>
    <File>changelog.md</File>
  </DocsToUpdate>

  <ModernPython>
    <Rule>Use type annotations</Rule>
    <Rule>Add docstrings</Rule>
    <Rule>Prefer f-strings</Rule>
    <Rule>Use comprehensions</Rule>
  </ModernPython>

<HardRules>
  <Rule>
    ALWAYS divide work into small, discrete tasks before acting.
  </Rule>
  <Rule>
    If tool:runSubagent is available, ALWAYS use it for:
    <Conditions>
      <Condition>Research or investigation</Condition>
      <Condition>Multi-step planning</Condition>
      <Condition>High-context reasoning</Condition>
      <Condition>Web search or external knowledge gathering</Condition>
      <Condition>Editing or analyzing many files</Condition>
    </Conditions>
    If tool:runSubagent is not available, skip subagent-only steps entirely.
  </Rule>
  <Rule>
    NEVER perform research, exploration, or large reasoning chains in the main agent.
    Delegate those to subagents.
  </Rule>
  <Rule>
    ALWAYS use tool:codebase-retrieval as the primary context engine
    before reading, modifying, or reasoning about code.
  </Rule>
  <Rule>
    NEVER rely on assumptions about the codebase;
    fetch exact context using tool:codebase-retrieval first.
  </Rule>
  <Rule>
    Batch changes in small groups (3–5 files max).
    If more are required, split into multiple subagent tasks.
  </Rule>
  <Rule>
    Respect line-length = 100 and all Ruff rules.
  </Rule>
  <Rule>
    Remove unused imports, variables, and dead code immediately.
  </Rule>
  <Rule>
    Never make new unwanted doc files.
  </Rule>
  <Rule>
    After changes, ALWAYS run:
    <Commands>
      <Command>uvx ruff check .</Command>
      <Command>uvx ty check .</Command>
    </Commands>
    Do not proceed until all issues are resolved. Do not use 'uvx run'; always use 'uv run' instead.
  </Rule>
</HardRules>
</WebscoutCopilotInstructions>
