<WebscoutCopilotInstructions>
  <Purpose>
    Concise, actionable guidance so an AI coding agent can be productive immediately when editing Webscout.
  </Purpose>

  <CriticalContextWindowManagement>
    <Rule>ALWAYS work in discrete, focused steps</Rule>
    <Rule>ALWAYS use runSubagent for  tasks</Rule>
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
  </TestingGuidelines>

  <DocsToUpdate>
    <File>docs/</File>
    <File>webscout/Provider/OPENAI/README.md</File>
    <File>README.md</File>
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
    ALWAYS use tool:runSubagent for:
    <Conditions>
      <Condition>Research or investigation</Condition>
      <Condition>Multi-step planning</Condition>
      <Condition>High-context reasoning</Condition>
      <Condition>Web search or external knowledge gathering</Condition>
      <Condition>Editing or analyzing many files</Condition>
    </Conditions>
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
    After changes, ALWAYS run:
    <Commands>
      <Command>uvx ruff check .</Command>
      <Command>uvx ty check .</Command>
    </Commands>
  </Rule>
</HardRules>
</WebscoutCopilotInstructions>
