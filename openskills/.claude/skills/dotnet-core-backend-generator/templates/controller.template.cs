using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;
using System.Threading;
using System.Threading.Tasks;
using System.Collections.Generic;

namespace Backend.API.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class {{EntityName}}Controller : ControllerBase
    {
        private readonly I{{EntityName}}Service _service;
        private readonly ILogger<{{EntityName}}Controller> _logger;

        public {{EntityName}}Controller(I{{EntityName}}Service service, ILogger<{{EntityName}}Controller> logger)
        {
            _service = service;
            _logger = logger;
        }

        [HttpGet("{id}")]
        public async Task<IActionResult> GetById(int id, CancellationToken cancellationToken)
        {
            var result = await _service.GetByIdAsync(id, cancellationToken);
            return result.IsSuccess ? Ok(result.Value) : NotFound(result.Error);
        }

        [HttpGet]
        public async Task<IActionResult> GetAll(CancellationToken cancellationToken)
        {
            var result = await _service.GetAllAsync(cancellationToken);
            return Ok(result.Value);
        }

        [HttpPost]
        public async Task<IActionResult> Create([FromBody] {{EntityName}}CreateDto dto, CancellationToken cancellationToken)
        {
            var result = await _service.CreateAsync(dto, cancellationToken);
            if (!result.IsSuccess) return BadRequest(result.Error);
            return CreatedAtAction(nameof(GetById), new { id = result.Value.Id }, result.Value);
        }

        [HttpPut("{id}")]
        public async Task<IActionResult> Update(int id, [FromBody] {{EntityName}}UpdateDto dto, CancellationToken cancellationToken)
        {
            var result = await _service.UpdateAsync(id, dto, cancellationToken);
            return result.IsSuccess ? Ok(result.Value) : BadRequest(result.Error);
        }

        [HttpDelete("{id}")]
        public async Task<IActionResult> Delete(int id, CancellationToken cancellationToken)
        {
            var result = await _service.DeleteAsync(id, cancellationToken);
            return result.IsSuccess ? NoContent() : BadRequest(result.Error);
        }
    }
}
