import { expect, mock, test } from 'claude-code/testing'

const band = (isWorking: boolean) =>
  ({
    plugin: 'clawd-buddy',
    component: 'AbovePrompt',
    props: {
      hasSurvey: false,
      isCollapsed: false,
      isWorking,
      maxRows: 10,
      bodyColumns: 60,
      scroll: { offset: 0, bodyRows: 9 },
      view: {},
    },
  }) as const

test('Clawd types while Claude works and idles after', async ($, on) => {
  const clock = mock.clock(on)
  on('command.register', () => ({ value: { command: 'clawd' } }))
  on('session.start', (_, e) => ({ cwd: e.cwd }))

  await $.session.start({ cwd: '/', surface: 'desktop', isInteractive: true })

  for (const surface of ['terminal', 'desktop', 'mobile'] as const) {
    const working = await $.ui.mount({ ...band(true), surface })
    expect((await working.find({ type: 'Text', text: /打字/ }))?.text).toContain('打字')
    await working.unmount()

    const resting = await $.ui.mount({ ...band(false), surface })
    expect((await resting.find({ type: 'Text', text: /待命/ }))?.text).toContain('待命')
    await resting.unmount()
  }

  // Eleven quiet minutes later, Clawd is tired.
  await clock.advance(11 * 60 * 1000)
  const later = await $.ui.mount({ ...band(false), surface: 'desktop' })
  expect((await later.find({ type: 'Text', text: /累/ }))?.text).toContain('累')
  await later.unmount()
})
